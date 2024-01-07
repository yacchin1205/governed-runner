import { paths } from "./schema";
import { endpoint, Pagination, toPageQuery, File } from "./types";

import { findFile } from "./files";

export const getJobs = async (
  pagination: Pagination | undefined = undefined
) => {
  const response: paths["/jobs/"]["get"]["responses"][200]["content"]["application/json"] =
    await fetch(`${endpoint}/jobs/${toPageQuery(pagination)}`, {
      method: "GET",
      credentials: "include",
    }).then((res) => res.json());
  return response;
};

async function getParentFolderLink(file: File) {
  const parentLink = file.links.find((link) => link.rel === "parent");
  if (parentLink) {
    return parentLink;
  }
  const { path } = file;
  let pathParts = path.split("/");
  if (pathParts.length === 1) {
    throw new Error("No parent folder found");
  }
  pathParts = pathParts.slice(0, pathParts.length - 1);
  let folder = await findFile(
    `${endpoint}/nodes/${file.node}/providers/${file.provider}/`,
    pathParts[0],
    undefined
  );
  if (!folder) {
    throw new Error("No parent folder found");
  }
  pathParts = pathParts.slice(1);
  while (pathParts.length > 0) {
    const filesLink = folder.links.find((link) => link.rel === "files");
    if (!filesLink) {
      throw new Error("No files link found");
    }
    folder = await findFile(filesLink.href, pathParts[0], undefined);
    if (!folder) {
      throw new Error("No parent folder found");
    }
    pathParts = pathParts.slice(1);
  }
  return folder.links.find((link) => link.rel === "files");
}

export const getCrates = async (
  file: File,
  pagination: Pagination | undefined = undefined
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
    throw new Error("No crate folder found");
  }
  const filesLink = crateFolder.links.find((link) => link.rel === "files");
  if (!filesLink) {
    throw new Error("No files link found");
  }
  const response: paths["/nodes/{node_id}/providers/{provider_id}/"]["get"]["responses"][200]["content"]["application/json"] =
    await fetch(`${filesLink.href}${toPageQuery(pagination)}`, {
      method: "GET",
      credentials: "include",
    }).then((res) => res.json());
  return response.items.filter((item) => item.name.startsWith(file.name));
};
