import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ButtonGroup from '../../components/ButtonGroup';

describe('ButtonGroup Component', () => {
  const defaultProps = {
    onOpenCamera: vi.fn(),
    onDemoBackend: vi.fn(),
    isModelReady: true,
    isLoading: false
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders both buttons', () => {
      render(<ButtonGroup {...defaultProps} />);

      expect(screen.getByRole('button', { name: /abrir cámara/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /demo backend/i })).toBeInTheDocument();
    });

    it('renders buttons with correct text', () => {
      render(<ButtonGroup {...defaultProps} />);

      expect(screen.getByText('Abrir Cámara')).toBeInTheDocument();
      expect(screen.getByText('Demo Backend')).toBeInTheDocument();
    });
  });

  describe('Button States', () => {
    it('disables buttons when isLoading is true', () => {
      render(<ButtonGroup {...defaultProps} isLoading={true} />);

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toBeDisabled();
      });
    });

    it('enables buttons when isLoading is false', () => {
      render(<ButtonGroup {...defaultProps} isLoading={false} />);

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).not.toBeDisabled();
      });
    });

    it('shows loading indicator when isLoading is true', () => {
      render(<ButtonGroup {...defaultProps} isLoading={true} />);

      expect(screen.getByText(/cargando/i)).toBeInTheDocument();
    });
  });

  describe('Button Clicks', () => {
    it('calls onOpenCamera when "Abrir Cámara" is clicked', async () => {
      const user = userEvent.setup();
      render(<ButtonGroup {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /abrir cámara/i }));

      expect(defaultProps.onOpenCamera).toHaveBeenCalledTimes(1);
    });

    it('calls onDemoBackend when "Demo Backend" is clicked', async () => {
      const user = userEvent.setup();
      render(<ButtonGroup {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /demo backend/i }));

      expect(defaultProps.onDemoBackend).toHaveBeenCalledTimes(1);
    });
  });

  describe('Visual Feedback', () => {
    it('applies primary style to "Abrir Cámara" button', () => {
      render(<ButtonGroup {...defaultProps} />);

      const cameraButton = screen.getByRole('button', { name: /abrir cámara/i });
      expect(cameraButton).toHaveClass('primary');
    });

    it('applies outline style to "Demo Backend" button', () => {
      render(<ButtonGroup {...defaultProps} />);

      const demoButton = screen.getByRole('button', { name: /demo backend/i });
      expect(demoButton).toHaveClass('outline');
    });
  });
});
