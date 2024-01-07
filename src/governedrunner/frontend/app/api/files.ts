import { paths } from "./schema";
import { endpoint, Pagination, toPageQuery, hasNextPage, File } from "./types";

type FindFileType = (
  filesLink: string,
  name: string,
  pagination: Pagination | undefined
) => Promise<File | null>;

export const findFile: FindFileType = async (
  filesLink: string,
  name: string,
  pagination: Pagination | undefined = undefined
) => {
  const response: paths["/nodes/{node_id}/providers/{provider_id}/"]["get"]["responses"][200]["content"]["application/json"] =
    await fetch(`${filesLink}${toPageQuery(pagination)}`, {
      method: "GET",
      credentials: "include",
    }).then((res) => res.json());
  const result = response.items.find((file) => file.name === name);
  if (result) {
    return result;
  }
  if (response.page && response.size && hasNextPage(response)) {
    return await findFile(filesLink, name, {
      page: response.page + 1,
      size: response.size,
    });
  }
  return null;
};
