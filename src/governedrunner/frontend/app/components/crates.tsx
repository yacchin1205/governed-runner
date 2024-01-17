import { useCallback, useEffect, useMemo, useState } from "react";

import { AppBar, Box, Toolbar, Button } from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import { PlayArrow } from "@mui/icons-material";

import { DataGrid } from "@mui/x-data-grid";
import { getCrates, getJobs } from "../api/crates";
import { createNotebookJob, createRunCrateJob } from "../api/jobs";
import { Pagination, File } from "../api/types";
import { Job, JobStatus } from "./job";

interface Param {
  defaultPageSize?: number | undefined;
  selectedFile?: File | undefined;
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

async function getCrate(crate: Job): Promise<string | null> {
  const crateLink = crate.links?.find((link) => link.rel === "download");
  const resp = await fetch(crateLink?.href as string);
  const data = await resp.json();
  return "completed";
}

export function CrateList({ defaultPageSize, selectedFile }: Param) {
  const [crates, setCrates] = useState<Job[]>([]);
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
      (crate) => crate.status === undefined && crate.links !== undefined
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
      getCrate(crate).then((status) => {
        setCrates(
          crates.map((c) => {
            if (c.id !== crate.id) {
              return c;
            }
            return Object.assign({}, c, {
              status,
            });
          })
        );
        setRequestedCrate(undefined);
      });
    }, STATUS_INTERVAL);
  }, [crates, requestedCrate]);

  useEffect(() => {
    // If the extension is .ipynb, get the execution result from RDM
    if (!selectedFile || !isNotebook(selectedFile)) {
      return;
    }
    if (selectedFile.id === loadedFile?.id) {
      return;
    }
    setCrates([]);
    getAllJobs(selectedFile, pagination).then((data) => {
      setLoadedFile(selectedFile);
      setCrates(data);
    });
  }, [selectedFile, loadedFile, pagination]);

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
    await createNotebookJob(selectedFile);
    setLoadedFile(undefined);
  }, [selectedFile]);

  const createRerunJob = useCallback(async (url: string) => {
    await createRunCrateJob(url);
    setLoadedFile(undefined);
  }, []);

  return (
    <Box sx={{ flexGrow: 1, height: "calc(100vh - 64px)", minWidth: "80vw" }}>
      <AppBar position="static" color="default">
        <Toolbar>
          <div>
            {selectedJob ? (
              <a onClick={() => setSelectedJob(null)}>{notebookName}</a>
            ) : (
              notebookName
            )}
            {selectedJob && <span> &gt; Job {selectedJob.id}</span>}
          </div>
          <Button
            color="inherit"
            startIcon={<RefreshIcon />}
            onClick={() => {
              setLoadedFile(undefined);
            }}
          >
            Reload
          </Button>
          {!selectedJob && (
            <Button
              color="inherit"
              startIcon={<PlayArrow />}
              onClick={createJob}
            >
              Run
            </Button>
          )}
        </Toolbar>
      </AppBar>
      {selectedJob && <JobStatus job={selectedJob} />}
      {!selectedJob && (
        <DataGrid
          rows={crates}
          onRowClick={(params) => {
            setSelectedJob(params.row);
          }}
          columns={[
            { field: "id", headerName: "ID", width: 70 },
            { field: "created_at", headerName: "Created", width: 200 },
            { field: "updated_at", headerName: "Updated", width: 200 },
            { field: "status", headerName: "Status", width: 200 },
            {
              field: "result",
              headerName: "Result",
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
