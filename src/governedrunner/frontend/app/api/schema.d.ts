/**
 * This file was auto-generated by openapi-typescript.
 * Do not make direct changes to the file.
 */


export interface paths {
  "/": {
    /**
     * Retrieve Server
     * @description このGoverned Runnerの情報です。
     */
    get: operations["retrieve_server__get"];
  };
  "/users/me": {
    /**
     * Retrieve Current User
     * @description 指定された認証情報に対応するユーザーを取得します。
     */
    get: operations["retrieve_current_user_users_me_get"];
  };
  "/jobs/": {
    /**
     * Retrieve Jobs
     * @description 現在のユーザーが実行した全てのジョブを取得します。
     */
    get: operations["retrieve_jobs_jobs__get"];
    /**
     * Create Job
     * @description ジョブを実行します。
     */
    post: operations["create_job_jobs__post"];
  };
  "/jobs/{job_id}": {
    /**
     * Retrieve Job
     * @description 指定されたジョブ情報を取得します。
     */
    get: operations["retrieve_job_jobs__job_id__get"];
  };
  "/nodes/": {
    /**
     * Retrieve Nodes
     * @description 現在のユーザーが参照可能なGakuNin RDMノードを取得します。
     */
    get: operations["retrieve_nodes_nodes__get"];
  };
  "/nodes/{node_id}/providers/": {
    /**
     * Retrieve Node Providers
     * @description 指定されたGakuNin RDMノードに紐づくストレージプロバイダを取得します。
     */
    get: operations["retrieve_node_providers_nodes__node_id__providers__get"];
  };
  "/nodes/{node_id}/children/": {
    /**
     * Retrieve Node Children
     * @description 指定されたGakuNin RDMノードの子ノードを取得します。
     */
    get: operations["retrieve_node_children_nodes__node_id__children__get"];
  };
  "/nodes/{node_id}/providers/{provider_id}/": {
    /**
     * Retrieve Node Root Files
     * @description 指定されたストレージプロバイダのルートディレクトリにあるファイルを取得します。
     */
    get: operations["retrieve_node_root_files_nodes__node_id__providers__provider_id___get"];
  };
  "/nodes/{node_id}/providers/{provider_id}/{filepath}": {
    /**
     * Retrieve Node Files
     * @description 指定されたストレージプロバイダのパスにあるファイルを取得します。
     */
    get: operations["retrieve_node_files_nodes__node_id__providers__provider_id___filepath__get"];
  };
}

export type webhooks = Record<string, never>;

export interface components {
  schemas: {
    /** Body_create_job_jobs__post */
    Body_create_job_jobs__post: {
      /** File Url */
      file_url: string;
      /** @default run-crate */
      type?: components["schemas"]["FileType"];
      /**
       * Use Snapshot
       * @default false
       */
      use_snapshot?: boolean;
    };
    /** CustomizedPage[FileOut] */
    CustomizedPage_FileOut_: {
      /** Items */
      items: components["schemas"]["FileOut"][];
      /** Total */
      total: number | null;
      /** Page */
      page: number | null;
      /** Size */
      size: number | null;
      /** Pages */
      pages?: number | null;
    };
    /** CustomizedPage[NodeOut] */
    CustomizedPage_NodeOut_: {
      /** Items */
      items: components["schemas"]["NodeOut"][];
      /** Total */
      total: number | null;
      /** Page */
      page: number | null;
      /** Size */
      size: number | null;
      /** Pages */
      pages?: number | null;
    };
    /** CustomizedPage[ProviderOut] */
    CustomizedPage_ProviderOut_: {
      /** Items */
      items: components["schemas"]["ProviderOut"][];
      /** Total */
      total: number | null;
      /** Page */
      page: number | null;
      /** Size */
      size: number | null;
      /** Pages */
      pages?: number | null;
    };
    /**
     * FileAction
     * @enum {string}
     */
    FileAction: "download" | "meta";
    /** FileOut */
    FileOut: {
      /**
       * Id
       * @example xxxxx
       */
      id: string;
      /**
       * Type
       * @example nodes
       */
      type: string;
      /**
       * Links
       * @example [
       *   {
       *     "href": "http://localhost:8000/nodes/xxxxx/",
       *     "rel": "children"
       *   }
       * ]
       */
      links: {
          [key: string]: string;
        }[];
      /** Data */
      data: unknown;
      kind: components["schemas"]["Kind"];
      /**
       * Name
       * @example file.txt
       */
      name: string;
      /**
       * Node
       * @example xxxxx
       */
      node: string;
      /**
       * Provider
       * @example osfstorage
       */
      provider: string;
      /**
       * Path
       * @example /path/to/file.txt
       */
      path: string;
      /**
       * Created At
       * @example 2021-01-01T00:00:00.000000+00:00
       */
      created_at: string | null;
      /**
       * Updated At
       * @example 2021-01-01T00:00:00.000000+00:00
       */
      updated_at: string | null;
      /** Content */
      content: unknown;
    };
    /**
     * FileType
     * @enum {string}
     */
    FileType: "run-crate" | "notebook";
    /** HTTPValidationError */
    HTTPValidationError: {
      /** Detail */
      detail?: components["schemas"]["ValidationError"][];
    };
    /** JobOut */
    JobOut: {
      /**
       * Id
       * @example JOB_ID
       */
      id: string;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /**
       * Updated At
       * Format: date-time
       */
      updated_at: string;
      status: components["schemas"]["State"] | null;
      source: components["schemas"]["SourceOut"] | null;
      result: components["schemas"]["ResultOut"] | null;
      progress: components["schemas"]["ProgressOut"] | null;
      /** Notebook */
      notebook: string | null;
    };
    /**
     * Kind
     * @enum {string}
     */
    Kind: "file" | "folder";
    /** NodeOut */
    NodeOut: {
      /**
       * Id
       * @example xxxxx
       */
      id: string;
      /**
       * Type
       * @example nodes
       */
      type: string;
      /**
       * Links
       * @example [
       *   {
       *     "href": "http://localhost:8000/nodes/xxxxx/",
       *     "rel": "children"
       *   }
       * ]
       */
      links: {
          [key: string]: string;
        }[];
      /** Data */
      data: unknown;
      /**
       * Title
       * @example GakuNin RDM Project
       */
      title: string;
    };
    /** Page[JobOut] */
    Page_JobOut_: {
      /** Items */
      items: components["schemas"]["JobOut"][];
      /** Total */
      total: number | null;
      /** Page */
      page: number | null;
      /** Size */
      size: number | null;
      /** Pages */
      pages?: number | null;
    };
    /** ProgressOut */
    ProgressOut: {
      /** Url */
      url: string | null;
    };
    /** ProviderOut */
    ProviderOut: {
      /**
       * Id
       * @example xxxxx
       */
      id: string;
      /**
       * Type
       * @example nodes
       */
      type: string;
      /**
       * Links
       * @example [
       *   {
       *     "href": "http://localhost:8000/nodes/xxxxx/",
       *     "rel": "children"
       *   }
       * ]
       */
      links: {
          [key: string]: string;
        }[];
      /** Data */
      data: unknown;
      /**
       * Node
       * @example xxxxx
       */
      node: string;
      /**
       * Name
       * @example osfstorage
       */
      name: string;
    };
    /** ResultOut */
    ResultOut: {
      /** Url */
      url: string | null;
    };
    /** ServerOut */
    ServerOut: {
      /**
       * Version
       * @example 0.0.1
       */
      version: string;
    };
    /** SourceOut */
    SourceOut: {
      /** Url */
      url: string | null;
    };
    /**
     * State
     * @enum {string}
     */
    State: "building" | "running" | "completed" | "failed";
    /** UserOut */
    UserOut: {
      /**
       * Id
       * @example 1
       */
      id: number;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /** Name */
      name: string;
    };
    /** ValidationError */
    ValidationError: {
      /** Location */
      loc: (string | number)[];
      /** Message */
      msg: string;
      /** Error Type */
      type: string;
    };
  };
  responses: never;
  parameters: never;
  requestBodies: never;
  headers: never;
  pathItems: never;
}

export type $defs = Record<string, never>;

export type external = Record<string, never>;

export interface operations {

  /**
   * Retrieve Server
   * @description このGoverned Runnerの情報です。
   */
  retrieve_server__get: {
    responses: {
      /** @description Successful Response */
      200: {
        content: {
          "application/json": components["schemas"]["ServerOut"];
        };
      };
    };
  };
  /**
   * Retrieve Current User
   * @description 指定された認証情報に対応するユーザーを取得します。
   */
  retrieve_current_user_users_me_get: {
    responses: {
      /** @description Successful Response */
      200: {
        content: {
          "application/json": components["schemas"]["UserOut"];
        };
      };
    };
  };
  /**
   * Retrieve Jobs
   * @description 現在のユーザーが実行した全てのジョブを取得します。
   */
  retrieve_jobs_jobs__get: {
    parameters: {
      query?: {
        state?: components["schemas"]["State"] | null;
        notebook?: string | null;
        /** @description Page number */
        page?: number;
        /** @description Page size */
        size?: number;
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        content: {
          "application/json": components["schemas"]["Page_JobOut_"];
        };
      };
      /** @description Validation Error */
      422: {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  /**
   * Create Job
   * @description ジョブを実行します。
   */
  create_job_jobs__post: {
    requestBody: {
      content: {
        "application/x-www-form-urlencoded": components["schemas"]["Body_create_job_jobs__post"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        content: {
          "application/json": components["schemas"]["JobOut"];
        };
      };
      /** @description Validation Error */
      422: {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  /**
   * Retrieve Job
   * @description 指定されたジョブ情報を取得します。
   */
  retrieve_job_jobs__job_id__get: {
    parameters: {
      path: {
        job_id: string;
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        content: {
          "application/json": components["schemas"]["JobOut"];
        };
      };
      /** @description Validation Error */
      422: {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  /**
   * Retrieve Nodes
   * @description 現在のユーザーが参照可能なGakuNin RDMノードを取得します。
   */
  retrieve_nodes_nodes__get: {
    parameters: {
      query?: {
        /** @description Page number */
        page?: number;
        size?: number;
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        content: {
          "application/json": components["schemas"]["CustomizedPage_NodeOut_"];
        };
      };
      /** @description Validation Error */
      422: {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  /**
   * Retrieve Node Providers
   * @description 指定されたGakuNin RDMノードに紐づくストレージプロバイダを取得します。
   */
  retrieve_node_providers_nodes__node_id__providers__get: {
    parameters: {
      query?: {
        /** @description Page number */
        page?: number;
        size?: number;
      };
      path: {
        node_id: string;
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        content: {
          "application/json": components["schemas"]["CustomizedPage_ProviderOut_"];
        };
      };
      /** @description Validation Error */
      422: {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  /**
   * Retrieve Node Children
   * @description 指定されたGakuNin RDMノードの子ノードを取得します。
   */
  retrieve_node_children_nodes__node_id__children__get: {
    parameters: {
      query?: {
        /** @description Page number */
        page?: number;
        size?: number;
      };
      path: {
        node_id: string;
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        content: {
          "application/json": components["schemas"]["CustomizedPage_NodeOut_"];
        };
      };
      /** @description Validation Error */
      422: {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  /**
   * Retrieve Node Root Files
   * @description 指定されたストレージプロバイダのルートディレクトリにあるファイルを取得します。
   */
  retrieve_node_root_files_nodes__node_id__providers__provider_id___get: {
    parameters: {
      query?: {
        /** @description Page number */
        page?: number;
        size?: number;
      };
      path: {
        node_id: string;
        provider_id: string;
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        content: {
          "application/json": components["schemas"]["CustomizedPage_FileOut_"];
        };
      };
      /** @description Validation Error */
      422: {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  /**
   * Retrieve Node Files
   * @description 指定されたストレージプロバイダのパスにあるファイルを取得します。
   */
  retrieve_node_files_nodes__node_id__providers__provider_id___filepath__get: {
    parameters: {
      query?: {
        action?: components["schemas"]["FileAction"] | null;
        /** @description Page number */
        page?: number;
        size?: number;
      };
      path: {
        node_id: string;
        provider_id: string;
        filepath: string;
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        content: {
          "application/json": components["schemas"]["CustomizedPage_FileOut_"];
        };
      };
      /** @description Validation Error */
      422: {
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
}
