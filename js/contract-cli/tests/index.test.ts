import { describe, it, expect, vi, beforeEach } from 'vitest';
import { buildCommandArgs, executeCommand, formatPayload } from '../index';
import { spawnSync } from 'child_process';

vi.mock('child_process', () => ({
  spawnSync: vi.fn(),
}));

describe('buildCommandArgs', () => {
  const baseArgs = ['-m', 'DICOM_reencoder.cli'];

  it('builds info command args', () => {
    const args = buildCommandArgs('info', '/path/to/file.dcm', undefined, {}, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'info', '/path/to/file.dcm', '--json']);
  });

  it('builds anonymize command args with inferred output', () => {
    const args = buildCommandArgs('anonymize', '/path/to/file.dcm', undefined, {}, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'anonymize', '/path/to/file.dcm', '-o', '/path/to/file_anon.dcm']);
  });

  it('builds anonymize command args with explicit output', () => {
    const args = buildCommandArgs('anonymize', '/path/to/file.dcm', '/output/anonymized.dcm', {}, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'anonymize', '/path/to/file.dcm', '-o', '/output/anonymized.dcm']);
  });

  it('builds to_image command args with default format', () => {
    const args = buildCommandArgs('to_image', '/path/to/file.dcm', undefined, {}, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'to_image', '/path/to/file.dcm', '--format', 'png', '-o', '/path/to/file.png']);
  });

  it('builds to_image command args with jpeg format', () => {
    const args = buildCommandArgs('to_image', '/path/to/file.dcm', undefined, { format: 'jpeg' }, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'to_image', '/path/to/file.dcm', '--format', 'jpeg', '-o', '/path/to/file.jpg']);
  });

  it('builds to_image command args with frame option', () => {
    const args = buildCommandArgs('to_image', '/path/to/file.dcm', undefined, { format: 'png', frame: 5 }, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'to_image', '/path/to/file.dcm', '--format', 'png', '-o', '/path/to/file.png', '--frame', '5']);
  });

  it('builds transcode command args with default syntax', () => {
    const args = buildCommandArgs('transcode', '/path/to/file.dcm', undefined, {}, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'transcode', '/path/to/file.dcm', '--syntax', 'explicit', '-o', '/path/to/file_transcoded.dcm']);
  });

  it('builds transcode command args with custom syntax', () => {
    const args = buildCommandArgs('transcode', '/path/to/file.dcm', undefined, { syntax: 'implicit' }, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'transcode', '/path/to/file.dcm', '--syntax', 'implicit', '-o', '/path/to/file_transcoded.dcm']);
  });

  it('builds validate command args', () => {
    const args = buildCommandArgs('validate', '/path/to/file.dcm', undefined, {}, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'validate', '/path/to/file.dcm', '--json']);
  });

  it('builds stats command args', () => {
    const args = buildCommandArgs('stats', '/path/to/file.dcm', undefined, {}, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'stats', '/path/to/file.dcm']);
  });

  it('builds dump command args', () => {
    const args = buildCommandArgs('dump', '/path/to/file.dcm', undefined, {}, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'info', '/path/to/file.dcm', '--json', '--verbose']);
  });

  it('builds volume command args with default output', () => {
    const args = buildCommandArgs('volume', '/path/to/file.dcm', undefined, {}, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'volume', '/path/to/file.dcm', '-o', 'output/volume.npy']);
  });

  it('builds volume command args with preview option', () => {
    const args = buildCommandArgs('volume', '/path/to/file.dcm', undefined, { preview: true }, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'volume', '/path/to/file.dcm', '-o', 'output/volume.npy', '--preview']);
  });

  it('builds nifti command args with default output', () => {
    const args = buildCommandArgs('nifti', '/path/to/file.dcm', undefined, {}, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'nifti', '/path/to/file.dcm', '-o', 'output/volume.nii.gz']);
  });

  it('builds nifti command args with series_uid option', () => {
    const args = buildCommandArgs('nifti', '/path/to/file.dcm', undefined, { series_uid: '1.2.3.4' }, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'nifti', '/path/to/file.dcm', '-o', 'output/volume.nii.gz', '--series-uid', '1.2.3.4']);
  });

  it('builds nifti command args with no_compress option', () => {
    const args = buildCommandArgs('nifti', '/path/to/file.dcm', undefined, { no_compress: true }, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'nifti', '/path/to/file.dcm', '-o', 'output/volume.nii.gz', '--no-compress']);
  });

  it('builds echo command args with default host and port', () => {
    const args = buildCommandArgs('echo', undefined, undefined, {}, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'echo', '127.0.0.1', '--port', '11112']);
  });

  it('builds echo command args with custom host and port', () => {
    const args = buildCommandArgs('echo', undefined, undefined, { host: '192.168.1.1', port: 9999 }, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'echo', '192.168.1.1', '--port', '9999']);
  });

  it('throws error for unsupported operation', () => {
    expect(() => {
      buildCommandArgs('unsupported_op' as any, '/path/to/file.dcm', undefined, {}, baseArgs);
    }).toThrow('Unsupported op: unsupported_op');
  });

  it('handles input path without directory', () => {
    const args = buildCommandArgs('anonymize', 'file.dcm', undefined, {}, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'anonymize', 'file.dcm', '-o', './file_anon.dcm']);
  });

  it('handles input path without extension', () => {
    const args = buildCommandArgs('anonymize', '/path/to/file', undefined, {}, baseArgs);
    expect(args).toEqual(['-m', 'DICOM_reencoder.cli', 'anonymize', '/path/to/file', '-o', '/path/to/file_anon.dcm']);
  });
});

describe('executeCommand', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls spawnSync with correct parameters', () => {
    const mockSpawnSync = vi.mocked(spawnSync);
    mockSpawnSync.mockReturnValue({
      status: 0,
      signal: null,
      output: ['', 'stdout', 'stderr'],
      stdout: 'stdout',
      stderr: 'stderr',
      pid: 12345,
    } as any);

    const result = executeCommand('python', ['-m', 'DICOM_reencoder.cli', 'info', 'file.dcm'], undefined);

    expect(mockSpawnSync).toHaveBeenCalledWith('python', ['-m', 'DICOM_reencoder.cli', 'info', 'file.dcm'], {
      encoding: 'utf-8',
    });
    expect(result.status).toBe(0);
  });
});

describe('formatPayload', () => {
  it('formats successful command payload', () => {
    const child = {
      status: 0,
      stdout: 'success output',
      stderr: '',
    } as any;

    const payload = formatPayload(child, '/output/file.dcm');

    expect(payload).toEqual({
      ok: true,
      returncode: 0,
      stdout: 'success output',
      stderr: '',
      output_files: ['/output/file.dcm'],
      metadata: null,
    });
  });

  it('formats failed command payload', () => {
    const child = {
      status: 1,
      stdout: '',
      stderr: 'error message',
    } as any;

    const payload = formatPayload(child);

    expect(payload).toEqual({
      ok: false,
      returncode: 1,
      stdout: '',
      stderr: 'error message',
      output_files: [],
      metadata: null,
    });
  });

  it('handles null stdout and stderr', () => {
    const child = {
      status: 0,
      stdout: null,
      stderr: null,
    } as any;

    const payload = formatPayload(child);

    expect(payload.stdout).toBe('');
    expect(payload.stderr).toBe('');
  });

  it('handles undefined status', () => {
    const child = {
      status: undefined,
      stdout: 'output',
      stderr: 'error',
    } as any;

    const payload = formatPayload(child);

    expect(payload.ok).toBe(false);
    expect(payload.returncode).toBe(1);
  });
});

