const configuredBackendUrl = import.meta.env.VITE_BACKEND_URL;

export const backendUrl =
  configuredBackendUrl ||
  `${window.location.protocol}//${window.location.hostname}:5001`;

