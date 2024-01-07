"use client";

import { useEffect, useMemo, useState } from "react";

import { Drawer, Box } from "@mui/material";

import { getCurrentUser } from "./api/user";
import { File } from "./api/types";
import { NotebookList } from "./components/notebooks";
import { CrateList, isNotebook } from "./components/crates";

const drawerWidth = 240;

export default function Home() {
  const [username, setUsername] = useState<string>();
  const [selectedFile, setSelectedFile] = useState<File | undefined>();

  const notebookOpened = useMemo(() => isNotebook(selectedFile), [selectedFile]);

  useEffect(() => {
    getCurrentUser().then((user) => {
      setUsername(user.name);
    });
  }, []);

  return (
    <Box sx={{ display: "flex" }}>
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
        <NotebookList
          onFileClick={(file) => {
            const webUrl = file.links.find((link) => link.rel === "web");
            console.log('Selected', webUrl);
            setSelectedFile(file);
          }}
        />
      </Drawer>

      <Box component="main">
        {notebookOpened && <CrateList defaultPageSize={10} selectedFile={selectedFile} />}
        {!notebookOpened && <div>Select a notebook</div>}
      </Box>
    </Box>
  );
}
