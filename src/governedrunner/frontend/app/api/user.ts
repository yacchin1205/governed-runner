import { paths } from './schema';

const endpoint = process.env.API_ENDPOINT || 'http://localhost:8000/api/v1';

export const getCurrentUser = async () => {
    const response: paths['/users/me']['get']['responses'][200]['content']['application/json'] =
        await fetch(`${endpoint}/users/me`, {
            method: 'GET',
            credentials: 'include',
        }).then((res) => res.json());
    return response;
};
