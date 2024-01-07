import { useEffect, useState, useMemo } from "react";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import { TreeView } from "@mui/x-tree-view/TreeView";

import { getNodes } from "../api/nodes";
import { Page, Pagination, Node } from "../api/types";
import { TreeItemExpander, NodeTreeItem, TreeItemHandlersParam } from "./tree";

interface Param extends TreeItemHandlersParam {
  defaultPageSize?: number | undefined;
}

export function NotebookList({
  defaultPageSize,
  onNodeClick,
  onProviderClick,
  onFileClick,
}: Param) {
  const pagination: Pagination | undefined = useMemo(
    () =>
      defaultPageSize !== undefined
        ? {
            size: defaultPageSize,
          }
        : undefined,
    [defaultPageSize]
  );
  const [nodes, setNodes] = useState<Node[]>([]);
  const [page, setPage] = useState<Page | undefined>(undefined);
  useEffect(() => {
    getNodes(pagination).then((data) => {
      setNodes(data.items);
      setPage(data);
    });
  }, [pagination]);
  return (
    nodes && (
      <TreeView
        aria-label="file system navigator"
        defaultCollapseIcon={<ExpandMoreIcon />}
        defaultExpandIcon={<ChevronRightIcon />}
        sx={{ height: 240, flexGrow: 1, maxWidth: 400, overflowY: "auto" }}
      >
        {nodes.map((node) => (
          <NodeTreeItem
            key={node.id}
            pagination={pagination}
            node={node}
            onNodeClick={onNodeClick}
            onProviderClick={onProviderClick}
            onFileClick={onFileClick}
          />
        ))}
        {page && page.page && page.pages && page.page < page.pages && (
          <TreeItemExpander
            nodeId="root-expand"
            onClick={async () => {
              if (!page.page || !page.size) {
                throw new Error("page or size is undefined");
              }
              const nextPage = page.page + 1;
              const data = await getNodes({ page: nextPage, size: page.size });
              setNodes(nodes.concat(data.items));
              setPage(data);
            }}
          />
        )}
      </TreeView>
    )
  );
}
