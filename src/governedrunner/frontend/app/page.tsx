"use client";

import { useEffect, useState } from 'react';

import { Drawer, Box } from '@mui/material';

import { getCurrentUser } from './api/user';
import { NotebookList } from './components/notebooks';

const drawerWidth = 240;

export default function Home() {
  const [username, setUsername] = useState<string>();

  useEffect(() => {
    getCurrentUser().then((user) => {
      setUsername(user.name);
    });
  }, []);

  return (
    <Box sx={{ display: 'flex' }}>
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <NotebookList
        onNodeClick={(node) => {
          console.log('Clicked node', node);
        }}
        onProviderClick={(provider) => {
          console.log('Clicked provider', provider);
        }}
        onFileClick={(file) => {
          console.log('Clicked file', file);
        }}
      />
    </Drawer>

    <Box
      component="main"
      sx={{ flexGrow: 1, bgcolor: 'background.default', p: 3 }}
    >
      <div>Main Content Here</div>
    </Box>
  </Box>
  )
}
