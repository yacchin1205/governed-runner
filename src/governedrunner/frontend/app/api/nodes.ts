import { paths } from './schema';

const endpoint = process.env.API_ENDPOINT || 'http://localhost:8000/api/v1';

export interface Pagination {
    page?: number;
    size?: number;
}

export interface Page {
    page?: number | null | number;
    pages?: number | null | number;
    size?: number | null | number;
}

export function toPageQuery(pagination: Pagination | undefined) {
    if (!pagination) {
        return '';
    }
    const { page, size } = pagination;
    if (size === undefined) {
        return `?page=${page || 1}`;
    }
    return `?page=${page || 1}&size=${size}`;
}

export function toNextPageQuery(page: Page) {
    if (!page.page) {
        throw new Error('page is undefined');
    }
    if (!page.pages) {
        throw new Error('pages is undefined');
    }
    if (!page.size) {
        throw new Error('size is undefined');
    }
    if (page.page >= page.pages) {
        return '';
    }
    return toPageQuery({ page: page.page + 1, size: page.size });
}

export const getNodes = async (
    pagination: Pagination | undefined = undefined
) => {
    const response: paths['/nodes/']['get']['responses'][200]['content']['application/json'] =
        await fetch(`${endpoint}/nodes/${toPageQuery(pagination)}`, {
            method: 'GET',
            credentials: 'include',
        }).then((res) => res.json());
    return response;
};
