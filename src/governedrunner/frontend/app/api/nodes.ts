import { paths } from "./schema";
import { endpoint, Pagination, toPageQuery } from "./types";

export const getNodes = async (
  pagination: Pagination | undefined = undefined
) => {
  const response: paths["/nodes/"]["get"]["responses"][200]["content"]["application/json"] =
    await fetch(`${endpoint}/nodes/${toPageQuery(pagination)}`, {
      method: "GET",
      credentials: "include",
    }).then((res) => res.json());
  return response;
};
