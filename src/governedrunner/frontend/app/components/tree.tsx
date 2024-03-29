import { useCallback, useMemo, useState } from "react";
import { TreeItem } from "@mui/x-tree-view/TreeItem";
import { CircularProgress } from "@mui/material";
import { Layers, Storage, Folder, Description } from "@mui/icons-material";

import {
  Page,
  Pagination,
  toPageQuery,
  toNextPageQuery,
  hasNextPage,
  Node,
  Provider,
  File,
  Link,
} from "../api/types";
import { paths } from "../api/schema";

interface Params {
  nodeId: string;
  onClick: () => Promise<void>;
}

function Loading() {
  return (
    <span className="gr-tree-loading">
      <CircularProgress size="16px" />
      <span className="gr-tree-loading-label">Loading...</span>
    </span>
  );
}

export function TreeItemExpander({ nodeId, onClick }: Params) {
  const [expanding, setExpanding] = useState(false);
  return (
    <TreeItem
      nodeId={nodeId}
      label={expanding ? <Loading /> : "More..."}
      onClick={() => {
        setExpanding(true);
        onClick().then(() => {
          setExpanding(false);
        });
      }}
    ></TreeItem>
  );
}
export interface TreeItemHandlersParam {
  onNodeClick?: (node: Node) => void;
  onProviderClick?: (provider: Provider) => void;
  onFileClick?: (file: File) => void;
  onError?: (err: any) => void;
}

interface LazyTreeItemParam extends TreeItemHandlersParam {
  nodeId: string;
  icon?: React.ReactNode;
  label: React.ReactNode;
  pagination?: Pagination | undefined;
  nodesLink?: Link | undefined;
  providersLink?: Link | undefined;
  filesLink?: Link | undefined;
  onItemClick?: () => void;
}

function LazyTreeItem({
  nodeId,
  icon,
  label,
  pagination,
  nodesLink,
  providersLink,
  filesLink,
  onItemClick,
  onNodeClick,
  onProviderClick,
  onFileClick,
  onError,
}: LazyTreeItemParam) {
  const [expanded, setExpanded] = useState(false);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [files, setFiles] = useState<File[]>([]);
  const [nextNodesPage, setNextNodesPage] = useState<Page | undefined>(
    undefined
  );
  const [nextProvidersPage, setNextProvidersPage] = useState<Page | undefined>(
    undefined
  );
  const [nextFilesPage, setNextFilesPage] = useState<Page | undefined>(
    undefined
  );

  const nextPageExists = useMemo(() => {
    return (
      (nextNodesPage && hasNextPage(nextNodesPage)) ||
      (nextProvidersPage && hasNextPage(nextProvidersPage)) ||
      (nextFilesPage && hasNextPage(nextFilesPage))
    );
  }, [nextNodesPage, nextProvidersPage, nextFilesPage]);

  const load = useCallback(
    async (
      nodesPageQuery: string | null,
      providersPageQuery: string | null,
      filesPageQuery: string | null
    ) => {
      try {
        if (nodesLink && nodesPageQuery !== null) {
          const res: paths["/nodes/{node_id}/children/"]["get"]["responses"][200]["content"]["application/json"] =
            await fetch(`${nodesLink.href}${nodesPageQuery}`, {
              method: "GET",
              credentials: "include",
            }).then((res) => res.json());
          setNodes(nodes.concat(res.items));
          setNextNodesPage(res);
        }
        if (providersLink && providersPageQuery !== null) {
          const res: paths["/nodes/{node_id}/providers/"]["get"]["responses"][200]["content"]["application/json"] =
            await fetch(`${providersLink.href}${providersPageQuery}`, {
              method: "GET",
              credentials: "include",
            }).then((res) => res.json());
          setProviders(providers.concat(res.items));
          setNextProvidersPage(res);
        }
        if (filesLink && filesPageQuery !== null) {
          const res: paths["/nodes/{node_id}/providers/{provider_id}/{filepath}"]["get"]["responses"][200]["content"]["application/json"] =
            await fetch(`${filesLink.href}${filesPageQuery}`, {
              method: "GET",
              credentials: "include",
            }).then((res) => res.json());
          setFiles(files.concat(res.items));
          setNextFilesPage(res);
        }
        setExpanded(true);
      } catch (error) {
        console.error(error);
        if (onError) {
          onError(error);
        }
      }
    },
    [nodesLink, providersLink, filesLink, nodes, providers, files, onError]
  );

  if (!(nodesLink || providersLink || filesLink)) {
    return (
      <TreeItem
        nodeId={nodeId}
        label={
          <>
            {icon} {label}
          </>
        }
        onClick={onItemClick}
      />
    );
  }
  return (
    <TreeItem
      nodeId={nodeId}
      label={
        <>
          {icon} {label}
        </>
      }
      onClick={() => {
        if (onItemClick) {
          onItemClick();
        }
        if (expanded) {
          return;
        }
        const defaultPageQuery = toPageQuery(pagination);
        load(defaultPageQuery, defaultPageQuery, defaultPageQuery).then(
          () => {}
        );
      }}
    >
      {nodes.map((node) => (
        <NodeTreeItem
          key={node.id}
          pagination={pagination}
          node={node}
          onNodeClick={onNodeClick}
          onProviderClick={onProviderClick}
          onFileClick={onFileClick}
          onError={onError}
        />
      ))}
      {providers.map((provider) => (
        <ProviderTreeItem
          key={provider.id}
          pagination={pagination}
          provider={provider}
          onNodeClick={onNodeClick}
          onProviderClick={onProviderClick}
          onFileClick={onFileClick}
          onError={onError}
        />
      ))}
      {files.map((file) => (
        <FileTreeItem
          key={file.id}
          pagination={pagination}
          file={file}
          onNodeClick={onNodeClick}
          onProviderClick={onProviderClick}
          onFileClick={onFileClick}
          onError={onError}
        />
      ))}
      {!expanded && (
        <TreeItem nodeId={`${nodeId}-expand`} label={<Loading />} />
      )}
      {nextPageExists && (
        <TreeItemExpander
          nodeId={`${nodeId}-more`}
          onClick={async () => {
            const nodesPageQuery = nextNodesPage
              ? toNextPageQuery(nextNodesPage)
              : null;
            const providersPageQuery = nextProvidersPage
              ? toNextPageQuery(nextProvidersPage)
              : null;
            const filesPageQuery = nextFilesPage
              ? toNextPageQuery(nextFilesPage)
              : null;
            await load(nodesPageQuery, providersPageQuery, filesPageQuery);
          }}
        />
      )}
    </TreeItem>
  );
}

interface NodeParams extends TreeItemHandlersParam {
  node: Node;
  pagination: Pagination | undefined;
}

export function NodeTreeItem({
  node,
  pagination,
  onNodeClick,
  onProviderClick,
  onFileClick,
  onError,
}: NodeParams) {
  const nodesLink = useMemo(
    () => node.links.find((link) => link.rel === "children"),
    [node]
  );
  const providersLink = useMemo(
    () => node.links.find((link) => link.rel === "providers"),
    [node]
  );

  return (
    <LazyTreeItem
      nodeId={node.id}
      icon={<Layers />}
      label={node.title}
      pagination={pagination}
      nodesLink={nodesLink}
      providersLink={providersLink}
      onNodeClick={onNodeClick}
      onProviderClick={onProviderClick}
      onFileClick={onFileClick}
      onItemClick={() => {
        if (!onNodeClick) {
          return;
        }
        onNodeClick(node);
      }}
      onError={onError}
    />
  );
}

interface ProviderParams extends TreeItemHandlersParam {
  provider: Provider;
  pagination: Pagination | undefined;
}

export function ProviderTreeItem({
  provider,
  pagination,
  onNodeClick,
  onProviderClick,
  onFileClick,
  onError,
}: ProviderParams) {
  const filesLink = useMemo(
    () => provider.links.find((link) => link.rel === "files"),
    [provider]
  );

  return (
    <LazyTreeItem
      nodeId={provider.id}
      icon={<Storage />}
      label={provider.name}
      pagination={pagination}
      filesLink={filesLink}
      onNodeClick={onNodeClick}
      onProviderClick={onProviderClick}
      onFileClick={onFileClick}
      onItemClick={() => {
        if (!onProviderClick) {
          return;
        }
        onProviderClick(provider);
      }}
      onError={onError}
    />
  );
}

interface FileParams extends TreeItemHandlersParam {
  file: File;
  pagination: Pagination | undefined;
}

export function FileTreeItem({
  file,
  pagination,
  onNodeClick,
  onProviderClick,
  onFileClick,
  onError,
}: FileParams) {
  const filesLink = useMemo(
    () => file.links.find((link) => link.rel === "files"),
    [file]
  );

  return (
    <LazyTreeItem
      nodeId={file.id}
      icon={file.kind === "folder" ? <Folder /> : <Description />}
      label={
        file.kind === "file" && !file.name.match(/.+\.ipynb$/i) ? (
          <span className="gr-other-file">{file.name}</span>
        ) : (
          file.name
        )
      }
      pagination={pagination}
      filesLink={filesLink}
      onNodeClick={onNodeClick}
      onProviderClick={onProviderClick}
      onFileClick={onFileClick}
      onItemClick={() => {
        if (!onFileClick) {
          return;
        }
        onFileClick(file);
      }}
      onError={onError}
    />
  );
}
