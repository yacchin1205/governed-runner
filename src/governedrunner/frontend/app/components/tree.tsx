import { useCallback, useMemo, useState } from "react";
import { TreeItem } from "@mui/x-tree-view/TreeItem";

import { Page, Pagination, toPageQuery, toNextPageQuery } from "../api/nodes";
import { paths } from "../api/schema";
import { on } from "events";

interface Params {
  nodeId: string;
  onClick: () => Promise<void>;
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
	name: string;
	links: Link[];
}

export interface File {
	id: string;
	name: string;
	links: Link[];
}

export function TreeItemExpander({ nodeId, onClick }: Params) {
  const [expanding, setExpanding] = useState(false);
  return (
    <TreeItem
      nodeId={nodeId}
      label={expanding ? "Loading..." : "More..."}
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
}

interface LazyTreeItemParam extends TreeItemHandlersParam {
	nodeId: string;
	label: string;
	pagination?: Pagination | undefined;
	nodesLink?: Link | undefined;
	providersLink?: Link | undefined;
	filesLink?: Link | undefined;
	onItemClick?: () => void;
}

function hasNextPage(page: Page): boolean {
	if (!page.page || !page.pages) {
		return false;
	}
	return page.page < page.pages;
}

function LazyTreeItem({
	nodeId, label, pagination, nodesLink, providersLink, filesLink,
	onItemClick, onNodeClick, onProviderClick, onFileClick,
}: LazyTreeItemParam) {
	const [expanded, setExpanded] = useState(false);
	const [nodes, setNodes] = useState<Node[]>([]);
	const [providers, setProviders] = useState<Provider[]>([]);
	const [files, setFiles] = useState<File[]>([]);
	const [nextNodesPage, setNextNodesPage] = useState<Page | undefined>(undefined);
	const [nextProvidersPage, setNextProvidersPage] = useState<Page | undefined>(undefined);
	const [nextFilesPage, setNextFilesPage] = useState<Page | undefined>(undefined);

	const nextPageExists = useMemo(() => {
		return (nextNodesPage && hasNextPage(nextNodesPage))
			|| (nextProvidersPage && hasNextPage(nextProvidersPage))
			|| (nextFilesPage && hasNextPage(nextFilesPage));
	}, [nextNodesPage, nextProvidersPage, nextFilesPage]);

	const load = useCallback(async (
		nodesPageQuery: string | null,
		providersPageQuery: string | null,
		filesPageQuery: string | null,
	) => {
		if (nodesLink && nodesPageQuery !== null) {
			const res: paths['/nodes/{node_id}/children/']['get']['responses'][200]['content']['application/json'] =
			await fetch(`${nodesLink.href}${nodesPageQuery}`, {
					method: 'GET',
					credentials: 'include',
			}).then((res) => res.json());
			setNodes(nodes.concat(res.items));
			setNextNodesPage(res);
		}
		if (providersLink && providersPageQuery !== null) {
			const res: paths['/nodes/{node_id}/providers/']['get']['responses'][200]['content']['application/json'] =
			await fetch(`${providersLink.href}${providersPageQuery}`, {
					method: 'GET',
					credentials: 'include',
			}).then((res) => res.json());
			setProviders(providers.concat(res.items));
			setNextProvidersPage(res);
		}
		if (filesLink && filesPageQuery !== null) {
			const res: paths['/nodes/{node_id}/providers/{provider_id}/{filepath}']['get']['responses'][200]['content']['application/json'] =
			await fetch(`${filesLink.href}${filesPageQuery}`, {
					method: 'GET',
					credentials: 'include',
			}).then((res) => res.json());
			setFiles(files.concat(res.items));
			setNextFilesPage(res);
		}
		setExpanded(true);
	}, [nodesLink, providersLink, filesLink, nodes, providers, files]);
	
	if (!(nodesLink || providersLink || filesLink)) {
		return <TreeItem
			nodeId={nodeId}
			label={label}
			onClick={onItemClick}
		/>;
	}
  return <TreeItem
		nodeId={nodeId}
		label={label}
		onClick={() => {
			if (onItemClick) {
				onItemClick();
			}
			if (expanded) {
				return;
			}
			const defaultPageQuery = toPageQuery(pagination);
			load(defaultPageQuery, defaultPageQuery, defaultPageQuery)
				.then(() => {});
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
			/>
		))}
    {!expanded &&
			<TreeItem
				nodeId={`${nodeId}-expand`}
				label={'Loading...'}
			/>
		}
		{nextPageExists &&
			<TreeItemExpander
				nodeId={`${nodeId}-more`}
				onClick={async () => {
					const nodesPageQuery = nextNodesPage ? toNextPageQuery(nextNodesPage) : null;
					const providersPageQuery = nextProvidersPage ? toNextPageQuery(nextProvidersPage) : null;
					const filesPageQuery = nextFilesPage ? toNextPageQuery(nextFilesPage) : null;
					await load(nodesPageQuery, providersPageQuery, filesPageQuery);
				}}
			/>
		}
  </TreeItem>;
}

interface NodeParams extends TreeItemHandlersParam {
	node: Node;
	pagination: Pagination | undefined;
}

export function NodeTreeItem({
	node, pagination,
	onNodeClick, onProviderClick, onFileClick,
}: NodeParams) {
	const nodesLink = useMemo(
		() => node.links.find((link) => link.rel === 'children'),
		[node],
	);
	const providersLink = useMemo(
		() => node.links.find((link) => link.rel === 'providers'),
		[node],
	);

  return <LazyTreeItem
		nodeId={node.id}
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
	/>;
}

interface ProviderParams extends TreeItemHandlersParam {
	provider: Provider;
	pagination: Pagination | undefined;
}

export function ProviderTreeItem({
	provider, pagination,
	onNodeClick, onProviderClick, onFileClick,
}: ProviderParams) {
	const filesLink = useMemo(
		() => provider.links.find((link) => link.rel === 'files'),
		[provider],
	);

  return <LazyTreeItem
		nodeId={provider.id}
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
	/>;
}

interface FileParams extends TreeItemHandlersParam {
	file: File;
	pagination: Pagination | undefined;
}

export function FileTreeItem({
	file, pagination,
	onNodeClick, onProviderClick, onFileClick,
}: FileParams) {
	const filesLink = useMemo(
		() => file.links.find((link) => link.rel === 'files'),
		[file],
	);

  return <LazyTreeItem
		nodeId={file.id}
		label={file.name}
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
	/>;
}