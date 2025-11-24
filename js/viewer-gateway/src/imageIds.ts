// Convert local/relative paths into wadouri: imageIds
export function buildImageIds(baseUrl: string, count: number) {
  const normalizedBase = baseUrl.replace(/\/$/, '');
  return Array.from({ length: count }, (_, i) => {
    const num = String(i + 1).padStart(4, '0');
    return `wadouri:${normalizedBase}/IM-0001-${num}.dcm`;
  });
}
