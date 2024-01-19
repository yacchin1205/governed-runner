import React, { useCallback, useState } from "react";

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
}

interface Params {
  job: Job;
}

export function JobStatus({ job }: Params) {
  const [status, setStatus] = useState(job.status);
  const [logs, setLogs] = useState<string[] | undefined>(undefined);
  //   const [statusInterval, setStatusInterval] = useState<number | null>(null);

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

  React.useEffect(() => {
    console.log("Job", job);
    if (logs === undefined && job.log) {
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
    console.log("Job progress", job.progress, websocketURL);
    const websocket = new WebSocket(websocketURL);
    websocket.addEventListener("message", onMessage);
    return () => {
      websocket.close();
      websocket.removeEventListener("message", onMessage);
    };
  }, [status, job, logs, onMessage]);

  return (
    <div>
      <div>
        Status: <span className="gr-job-status-indicator">{status}</span>
      </div>
      <div>
        Created:{" "}
        <span className="gr-job-status-indicator">{job.created_at}</span>
      </div>
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
