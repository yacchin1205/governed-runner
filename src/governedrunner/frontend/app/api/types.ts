export const endpoint =
  process.env.API_ENDPOINT || "http://localhost:8000/api/v1";

export interface Pagination {
  page?: number;
  size?: number;
}

export interface Page {
  page?: number | null | number;
  pages?: number | null | number;
  size?: number | null | number;
}

export function hasNextPage(page: Page): boolean {
  if (!page.page || !page.pages) {
    return false;
  }
  return page.page < page.pages;
}

export function toPageQuery(pagination: Pagination | undefined) {
  if (!pagination) {
    return "";
  }
  const { page, size } = pagination;
  if (size === undefined) {
    return `?page=${page || 1}`;
  }
  return `?page=${page || 1}&size=${size}`;
}

export function toNextPageQuery(page: Page) {
  if (!page.page) {
    throw new Error("page is undefined");
  }
  if (!page.pages) {
    throw new Error("pages is undefined");
  }
  if (!page.size) {
    throw new Error("size is undefined");
  }
  if (page.page >= page.pages) {
    return "";
  }
  return toPageQuery({ page: page.page + 1, size: page.size });
}

export interface Link {
  [key: string]: string;
}

export interface Node {
  id: string;
  title: string;
  links: Link[];
}

export interface Provider {
  id: string;
  node: string;
  name: string;
  links: Link[];
}

export interface File {
  id: string;
  kind: "file" | "folder";
  node: string;
  provider: string;
  name: string;
  path: string;
  created_at: string;
  updated_at: string;
  links: Link[];
}
