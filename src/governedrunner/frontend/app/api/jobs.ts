import { paths } from "./schema";

import { endpoint, Pagination, toPageQuery, hasNextPage, File } from "./types";

export const createNotebookJob = async (
  file: File,
  pagination: Pagination | undefined = undefined
) => {
  const webLink = file.links.find((link) => link.rel === "web");
  if (!webLink) {
    throw new Error("No web link found");
  }
  const formData = new FormData();
  formData.append("file_url", webLink.href);
  formData.append("type", "notebook");
  const response: paths["/jobs/"]["post"]["responses"][200]["content"]["application/json"] =
    await fetch(`${endpoint}/jobs/${toPageQuery(pagination)}`, {
      method: "POST",
      credentials: "include",
      body: formData,
    }).then((res) => res.json());
  return response;
};
