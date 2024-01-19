"use client";

import { useEffect, useMemo, useState, useCallback } from "react";

import { Drawer, Box, AppBar, Toolbar, Typography, Alert } from "@mui/material";

import { getCurrentUser } from "./api/user";
import { File } from "./api/types";
import { NotebookList } from "./components/notebooks";
import { CrateList, isNotebook } from "./components/crates";

const drawerWidth = 300;

export default function Home() {
  const [username, setUsername] = useState<string>();
  const [selectedFile, setSelectedFile] = useState<File | undefined>();
  const [error, setError] = useState<string | undefined>(undefined);

  const notebookOpened = useMemo(
    () => isNotebook(selectedFile),
    [selectedFile]
  );

  useEffect(() => {
    getCurrentUser().then((user) => {
      setUsername(user.name);
    });
  }, []);

  const onError = useCallback((err: any) => {
    console.error("Error", err);
    setError(err.toString());
  }, []);

  return (
    <Box sx={{ display: "flex" }}>
      <AppBar
        className="gr-app-bar"
        position="fixed"
        sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}
      >
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Governed Run Manager
          </Typography>
          <div className="gr-toolbar-button">
            <a href="/">JupyterHub</a>
          </div>
          <div>{username}</div>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            boxSizing: "border-box",
          },
        }}
      >
        <Toolbar />
        <NotebookList
          onError={onError}
          onFileClick={(file) => {
            const webUrl = file.links.find((link) => link.rel === "web");
            console.log("Selected", webUrl);
            setSelectedFile(file);
          }}
        />
      </Drawer>

      <Box component="main">
        <Toolbar />
        {error && (
          <Alert severity="error" onClose={() => setError(undefined)}>
            {error}
          </Alert>
        )}
        {notebookOpened && (
          <CrateList
            defaultPageSize={50}
            selectedFile={selectedFile}
            onError={onError}
          />
        )}
        {!notebookOpened && (
          <div className="gr-no-notebook">Select a notebook</div>
        )}
      </Box>
    </Box>
  );
}
