export interface ProblemFieldIssue {
  field: string;
  message: string;
  type: string;
}

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string;
  code: string;
  request_id?: string;
  errors?: ProblemFieldIssue[];
}
