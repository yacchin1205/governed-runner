import { paths } from "./schema";
import { endpoint, Pagination, toPageQuery, File } from "./types";

import { findFile } from "./files";
import { Link } from "./types";

export type CrateFile = {
  notebook: string;
  id: string;
  created_at: string | null;
  updated_at: string | null;
  name?: string;
  status?: "running" | "completed" | "failed" | null;
  links?: Link[];
  log?: string;
  progress: {
    url: string | null;
  } | null;
}

export const getJobs = async (
  notebook: File | undefined = undefined,
  pagination: Pagination | undefined = undefined
) => {
  let query = toPageQuery(pagination);
  if (notebook) {
    if (query) {
      query += "&";
    } else {
      query += "?";
    }
    const path = notebook.path.match(/^\/.+/) ? notebook.path.substring(1) : notebook.path;
    query += `notebook=${path}`;
  }
  const response: paths["/jobs/"]["get"]["responses"][200]["content"]["application/json"] =
    await fetch(`${endpoint}/jobs/${query}`, {
      method: "GET",
      credentials: "include",
    }).then((res) => res.json());
  return response;
};

async function getParentFolderLink(file: File) {
  return {
    href: `${endpoint}/nodes/${file.node}/providers/${file.provider}/`,
  };
}

export const getCrates = async (
  file: File,
) => {
  const parentFolderLink = await getParentFolderLink(file);
  if (!parentFolderLink) {
    throw new Error("No parent folder found");
  }
  const crateFolder = await findFile(
    parentFolderLink.href,
    ".crates",
    undefined
  );
  if (!crateFolder) {
    console.warn("No crate folder found");
    return [];
  }
  const filesLink = crateFolder.links.find((link) => link.rel === "files");
  if (!filesLink) {
    throw new Error("No files link found");
  }
  const indexFile = await findFile(
    filesLink.href,
    "index.json",
    undefined
  );
  if (!indexFile) {
    return [];
  }
  const downloadLink = indexFile.links.find((link) => link.rel === "download");
  if (!downloadLink) {
    throw new Error("No download link found");
  }
  const indexData: paths["/nodes/{node_id}/providers/{provider_id}/"]["get"]["responses"][200]["content"]["application/json"] = await fetch(downloadLink.href, {
    method: "GET",
    credentials: "include",
  }).then((res) => res.json());
  const crates: CrateFile[] = indexData.items[0].content as CrateFile[];
  const path = file.path.match(/^\/.+/) ? file.path.substring(1) : file.path;
  return crates.filter((crate) => crate.notebook === path);
};
