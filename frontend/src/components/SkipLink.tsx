/** WCAG 2.4.1 Bypass Blocks. First focusable element in the DOM. */
export function SkipLink() {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-sidebar focus:px-4 focus:py-2 focus:text-white"
    >
      Skip to main content
    </a>
  );
}
