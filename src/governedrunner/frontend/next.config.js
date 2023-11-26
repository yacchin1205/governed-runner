/** @type {import('next').NextConfig} */
const nextConfig = {
    // Configuration w/ JupyterHub
    output: 'export',
    basePath: '/services/Governed-Run',
    assetPrefix: '/services/Governed-Run/',
    env: {
        API_ENDPOINT: '/services/Governed-Run/api/v1',
    },
    /*
    // Configuration w/ dev-server
    output: 'export',
    env: {
        API_ENDPOINT: 'http://localhost:8000/api/v1',
    },
    */
    /*
    // Configuration w/ npm run start
    env: {
        API_ENDPOINT: 'http://localhost:8000/api/v1',
    },
    */
}

module.exports = nextConfig
