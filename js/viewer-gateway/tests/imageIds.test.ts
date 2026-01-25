import { describe, it, expect } from 'vitest';
import { buildImageIds } from '../src/imageIds';

describe('buildImageIds', () => {
  it('generates correct imageIds with base URL', () => {
    const baseUrl = 'http://localhost:8080/sample_series';
    const count = 3;
    const result = buildImageIds(baseUrl, count);

    expect(result).toHaveLength(3);
    expect(result[0]).toBe('wadouri:http://localhost:8080/sample_series/IM-0001-0001.dcm');
    expect(result[1]).toBe('wadouri:http://localhost:8080/sample_series/IM-0001-0002.dcm');
    expect(result[2]).toBe('wadouri:http://localhost:8080/sample_series/IM-0001-0003.dcm');
  });

  it('removes trailing slash from base URL', () => {
    const baseUrl = 'http://localhost:8080/sample_series/';
    const count = 2;
    const result = buildImageIds(baseUrl, count);

    expect(result[0]).toBe('wadouri:http://localhost:8080/sample_series/IM-0001-0001.dcm');
    expect(result[1]).toBe('wadouri:http://localhost:8080/sample_series/IM-0001-0002.dcm');
  });

  it('pads numbers with zeros correctly', () => {
    const baseUrl = 'http://test';
    const count = 174;
    const result = buildImageIds(baseUrl, count);

    expect(result[0]).toBe('wadouri:http://test/IM-0001-0001.dcm');
    expect(result[9]).toBe('wadouri:http://test/IM-0001-0010.dcm');
    expect(result[99]).toBe('wadouri:http://test/IM-0001-0100.dcm');
    expect(result[173]).toBe('wadouri:http://test/IM-0001-0174.dcm');
  });

  it('handles single image', () => {
    const baseUrl = 'http://test';
    const count = 1;
    const result = buildImageIds(baseUrl, count);

    expect(result).toHaveLength(1);
    expect(result[0]).toBe('wadouri:http://test/IM-0001-0001.dcm');
  });

  it('handles empty count', () => {
    const baseUrl = 'http://test';
    const count = 0;
    const result = buildImageIds(baseUrl, count);

    expect(result).toHaveLength(0);
    expect(result).toEqual([]);
  });

  it('handles relative paths', () => {
    const baseUrl = '/sample_series';
    const count = 2;
    const result = buildImageIds(baseUrl, count);

    expect(result[0]).toBe('wadouri:/sample_series/IM-0001-0001.dcm');
    expect(result[1]).toBe('wadouri:/sample_series/IM-0001-0002.dcm');
  });

  it('handles base URL with multiple trailing slashes', () => {
    const baseUrl = 'http://test///';
    const count = 1;
    const result = buildImageIds(baseUrl, count);

    expect(result[0]).toBe('wadouri:http://test///IM-0001-0001.dcm');
  });
});

