import { useCallback, useEffect, useMemo, useState } from "react";

import { AppBar, Box, Toolbar, Button, CircularProgress } from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import { OpenInNew, PlayArrow } from "@mui/icons-material";

import { DataGrid } from "@mui/x-data-grid";
import { getCrates, getJobs } from "../api/crates";
import { createNotebookJob, createRunCrateJob } from "../api/jobs";
import { paths } from "../api/schema";
import { Pagination, File } from "../api/types";
import { Job, JobStatus, toAPIURL, getRDMURL } from "./job";

interface Param {
  defaultPageSize?: number | undefined;
  selectedFile?: File | undefined;
  onError: (err: any) => void;
}

interface RDMRef {
  url: string | null;
}

const STATUS_INTERVAL = 100;

export function isNotebook(file: File | undefined): boolean {
  if (!file) {
    return false;
  }
  if (file.kind !== "file") {
    return false;
  }
  return file.name.endsWith(".ipynb");
}

async function getAllJobs(
  selectedFile: File,
  pagination: Pagination | undefined
): Promise<Job[]> {
  let jobs: Job[] = [];
  jobs = jobs.concat(
    await getCrates(selectedFile).then((data) =>
      data.map((crate) =>
        Object.assign({}, crate, {
          result:
            crate.links && crate.links.find((link) => link.rel === "web")?.href,
        })
      )
    )
  );
  const runningJobs = await getJobs(selectedFile, pagination).then(
    (data) => data.items
  );
  jobs = jobs.concat(
    runningJobs.filter(
      (job) => !jobs.some((crate) => crate.id.includes(job.id))
    )
  );
  return jobs
    .sort((a, b) => {
      if (!a.created_at) {
        return -1;
      }
      if (!b.created_at) {
        return 1;
      }
      return a.created_at.localeCompare(b.created_at);
    })
    .reverse();
}

async function getCrate(crate: Job): Promise<any> {
  const wbLink = crate.links?.find((link) => link.rel === "download");
  if (!wbLink) {
    throw new Error("No download link");
  }
  const crateLink = `${toAPIURL(wbLink.href)}?action=download`;
  const resp = await fetch(crateLink);
  const data: paths["/nodes/{node_id}/providers/{provider_id}/"]["get"]["responses"][200]["content"]["application/json"] =
    await resp.json();
  if (data.items.length === 0) {
    throw new Error(`Load failed: ${crateLink}`);
  }
  const content: any = data.items[0].content;
  const outputEntities = content["@graph"].filter(
    (e: any) => e["@type"] === "File" && e["@id"].match(/^output-.+\.ipynb$/)
  );
  if (outputEntities.length === 0) {
    return { content };
  }
  const outputWeb = await getRDMURL(outputEntities[0]["rdmURL"]);
  return { content: data.items[0].content, outputWeb };
}

export function CrateList({ defaultPageSize, selectedFile, onError }: Param) {
  const [crates, setCrates] = useState<Job[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadedFile, setLoadedFile] = useState<File | undefined>();
  const [requestedCrate, setRequestedCrate] = useState<Job | undefined>();
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const pagination: Pagination | undefined = useMemo(
    () =>
      defaultPageSize !== undefined
        ? {
            size: defaultPageSize,
          }
        : undefined,
    [defaultPageSize]
  );
  const notebookName = useMemo(
    () =>
      selectedFile
        ? selectedFile.path.match(/^\/.+/)
          ? selectedFile.path.substring(1)
          : selectedFile.path
        : null,
    [selectedFile]
  );

  useEffect(() => {
    const newCrates = crates.filter(
      (crate) => crate.log === undefined && crate.links !== undefined
    );
    if (newCrates.length === 0) {
      return;
    }
    const crate = newCrates[0];
    if (crate.id === requestedCrate?.id) {
      return;
    }
    setRequestedCrate(crate);
    setTimeout(() => {
      getCrate(crate)
        .then(({ content, outputWeb }) => {
          if (!content) {
            setRequestedCrate(undefined);
            return;
          }
          const logEntities = content["@graph"].filter(
            (e: any) =>
              e["@type"] === "File" && e["@id"].match(/^runner-.+\.log$/)
          );
          const outputEntities = content["@graph"].filter(
            (e: any) =>
              e["@type"] === "File" && e["@id"].match(/^output-.+\.ipynb$/)
          );
          const extra: any = {};
          if (logEntities.length > 0) {
            extra.log = logEntities[0]["text"];
          }
          if (outputEntities.length > 0) {
            extra.output = outputEntities[0]["rdmURL"];
          }
          if (outputWeb) {
            extra.outputWeb = outputWeb;
          }
          setCrates(
            crates.map((c) => {
              if (c.id !== crate.id) {
                return c;
              }
              return Object.assign({}, c, extra);
            })
          );
          setRequestedCrate(undefined);
        })
        .catch((err) => {
          console.log(err);
          if (onError) {
            onError(err);
          }
          setRequestedCrate(undefined);
        });
    }, STATUS_INTERVAL);
  }, [crates, requestedCrate, onError]);

  useEffect(() => {
    // If the extension is .ipynb, get the execution result from RDM
    if (!selectedFile || !isNotebook(selectedFile)) {
      return;
    }
    if (selectedFile.id === loadedFile?.id) {
      return;
    }
    setCrates([]);
    setLoading(true);
    getAllJobs(selectedFile, pagination)
      .then((data) => {
        setLoadedFile(selectedFile);
        setCrates(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        if (onError) {
          onError(err);
        }
        setLoading(false);
      });
  }, [selectedFile, loadedFile, pagination, onError]);

  const createJob = useCallback(async () => {
    if (!selectedFile) {
      return;
    }
    if (selectedFile.kind !== "file") {
      return;
    }
    if (!selectedFile.name.endsWith(".ipynb")) {
      return;
    }
    try {
      await createNotebookJob(selectedFile);
      setLoadedFile(undefined);
    } catch (err) {
      console.error(err);
      if (onError) {
        onError(err);
      }
    }
  }, [selectedFile, onError]);

  const createRerunJob = useCallback(async (url: string) => {
    try {
      await createRunCrateJob(url);
      setLoadedFile(undefined);
    } catch (err) {
      console.error(err);
      if (onError) {
        onError(err);
      }
    }
  }, [onError]);

  return (
    <Box
      sx={{
        flexGrow: 1,
        height: "calc(100vh - 64px)",
        width: "calc(100vw - 300px)",
      }}
    >
      <AppBar position="static" color="default">
        <Toolbar>
          <div className="gr-toolbar-notebook-label">
            {selectedJob ? (
              <a onClick={() => setSelectedJob(null)}>{notebookName}</a>
            ) : (
              notebookName
            )}
            {selectedJob && <span> &gt; Job {selectedJob.id}</span>}
          </div>
          {!selectedJob && (
            <Button
              color="inherit"
              startIcon={<PlayArrow />}
              onClick={createJob}
            >
              Run
            </Button>
          )}
          {!selectedJob && (
            <Button
              color="inherit"
              startIcon={<RefreshIcon />}
              onClick={() => {
                setLoadedFile(undefined);
              }}
            >
              Reload
            </Button>
          )}
        </Toolbar>
      </AppBar>
      {selectedJob && <JobStatus job={selectedJob} />}
      {crates.length === 0 && loading && (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            height: "100%",
          }}
        >
          <CircularProgress />
        </Box>
      )}
      {!selectedJob && (crates.length > 0 || loading === false) && (
        <DataGrid
          rows={crates}
          onRowClick={(params) => {
            setSelectedJob(params.row);
          }}
          columns={[
            { field: "id", headerName: "ID", width: 200 },
            { field: "created_at", headerName: "Created", width: 200 },
            { field: "updated_at", headerName: "Updated", width: 200 },
            { field: "status", headerName: "Status", width: 200 },
            {
              field: "outputWeb",
              headerName: "Output",
              renderCell: (params) => {
                if (params.row.status !== "completed") {
                  return <></>;
                }
                if (params.row.links === undefined) {
                  return <></>;
                }
                if (params.value === undefined) {
                  return <CircularProgress size={18} />;
                }
                if (params.value === null) {
                  return <CircularProgress size={18} />;
                }
                return (
                  <Button
                    href={params.value}
                    variant="contained"
                    size="small"
                    color="inherit"
                    startIcon={<OpenInNew />}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open
                  </Button>
                );
              },
              width: 200,
            },
            {
              field: "result",
              headerName: "Action",
              renderCell: (params) =>
                typeof params.value === "string" ? (
                  <>
                    <Button
                      variant="contained"
                      size="small"
                      color="inherit"
                      startIcon={<PlayArrow />}
                      onClick={() => createRerunJob(params.value as string)}
                    >
                      Re-run
                    </Button>
                  </>
                ) : (
                  <></>
                ),
              width: 200,
            },
          ]}
          checkboxSelection
        />
      )}
    </Box>
  );
}
