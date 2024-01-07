import { paths } from "./schema";
import { endpoint } from "./types";

export const getCurrentUser = async () => {
  const response: paths["/users/me"]["get"]["responses"][200]["content"]["application/json"] =
    await fetch(`${endpoint}/users/me`, {
      method: "GET",
      credentials: "include",
    }).then((res) => res.json());
  return response;
};
