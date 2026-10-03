export type DocumentSummary = {
  id: string;
  title: string;
  uri: string;
};

export type DocumentDetail = DocumentSummary & {
  content: string;
};

export type PromptName = 'summarize' | 'format';

export type PromptResponse = {
  name: PromptName;
  doc_id: string;
  text: string;
};

export type EditResponse = {
  message: string;
  document: DocumentDetail;
};

export type HealthResponse = {
  status: string;
  server: string;
  transport: string;
};

export type ActivityEntry = {
  title: string;
  detail: string;
};
