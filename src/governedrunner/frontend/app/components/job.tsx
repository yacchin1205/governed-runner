import React, { useCallback, useState, useEffect } from "react";

import { paths } from "../api/schema";
import { endpoint, Link } from "../api/types";

export interface Job {
  id: string;
  created_at: string | null;
  updated_at: string | null;
  name?: string;
  status?: "running" | "building" | "completed" | "failed" | null;
  links?: Link[];
  progress?: {
    url: string | null;
  } | null;
  log?: string | null;
  output?: string | null;
  outputWeb?: string | null;
}

interface Params {
  job: Job;
  onError?: (err: any) => void;
}

export function toAPIURL(wbURL: string): string {
  const wbMatch = wbURL.match(/.+\/resources\/(.+)\/providers\/(.+)/);
  if (!wbMatch) {
    throw new Error(`Invalid download link: ${wbURL}`);
  }
  return `${endpoint}/nodes/${wbMatch[1]}/providers/${wbMatch[2]}`;
}

export async function getRDMURL(wbURL: string): Promise<string> {
  const apiURL = toAPIURL(wbURL);
  const response = await fetch(apiURL);
  const data: paths["/nodes/{node_id}/providers/{provider_id}/"]["get"]["responses"][200]["content"]["application/json"] =
    await response.json();
  if (data.items.length === 0) {
    throw new Error(`Load failed: ${apiURL}`);
  }
  return data.items[0].links.find((link) => link.rel === "web")?.href || "";
}

export function JobStatus({ job, onError }: Params) {
  const [status, setStatus] = useState(job.status);
  const [notebookURL, setNotebookURL] = useState<string | undefined>(undefined);
  const [logs, setLogs] = useState<string[] | undefined>(undefined);

  const onMessage = useCallback(
    (event: MessageEvent<string>) => {
      const data = JSON.parse(event.data);
      if (data.status) {
        setStatus(data.status);
      }
      if (data.log === undefined) {
        setLogs(undefined);
        return;
      }
      if (!logs) {
        setLogs([data.log]);
        return;
      }
      setLogs([...logs, data.log]);
    },
    [logs]
  );

  useEffect(() => {
    if (logs === undefined && job.log !== undefined && job.log !== null) {
      setLogs([job.log]);
    }
    if (!job.progress || !job.progress.url) {
      return;
    }
    let baseURL = endpoint;
    if (baseURL.match(/^\/.*/)) {
      baseURL = new URL(baseURL, window.location.href).toString();
    }
    const url = new URL(job.progress.url, baseURL);
    url.protocol = url.protocol.replace("http", "ws");
    const websocketURL = url.toString();
    const websocket = new WebSocket(websocketURL);
    websocket.addEventListener("message", onMessage);
    return () => {
      websocket.close();
      websocket.removeEventListener("message", onMessage);
    };
  }, [status, job, logs, onMessage]);

  useEffect(() => {
    if (!job.output) {
      return;
    }
    getRDMURL(job.output)
      .then((url) => {
        setNotebookURL(url);
      })
      .catch((err) => {
        console.error(err);
        if (onError) {
          onError(err);
        }
      });
  }, [job, onError]);

  return (
    <div>
      <div>
        Status: <span className="gr-job-status-indicator">{status}</span>
      </div>
      <div>
        Created:{" "}
        <span className="gr-job-status-indicator">{job.created_at}</span>
      </div>
      {notebookURL && (
        <div>
          Output: <a href={notebookURL}>{notebookURL}</a>
        </div>
      )}
      <div>Logs:</div>
      {logs === undefined && <div className="gr-job-no-status">No logs</div>}
      {logs !== undefined && (
        <div className="gr-job-status">
          <pre>{logs?.join("")}</pre>
        </div>
      )}
    </div>
  );
}
