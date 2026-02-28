# Task 0049: New Feature: UI Improvements: change top navigation bar to a collapsible Sidepanel
- Session File: @task-0049-new-feature-ui-side-panel-new-start-3-full-session.md
- IDE: Claude Code - Plan Mode
- Date: 2025-11-08
- Model: Claude Sonnet 4.5


## Overview

This task introduces a new navigational pattern to the frontend UI, moving from a top navigation bar (@frontend/src/components/layout/header.tsx) to a left-hand, collapsible side panel. The goal is to align the application layout with the latest Figma design, which specifies a vertical navigation experience with both expanded and collapsed states.

- The legacy sidebar component (@frontend/src/components/layout/sidebar.tsx) is likely unused and should be confirmed and removed if so.
- The new side panel component will be built from scratch, not based on any pre-existing sidebar code.
- The menu options and navigation logic from the current header will be migrated to the new vertical side panel.
- The component must support toggling between collapsed and expanded states, matching Figma specifications.

## Basic Requirements v1

### Requirement 1: Replace Top Navigation with Side Panel
- Remove the top navigation bar and replace it by integrating a collapsible side panel on the left in the main layout.
- Ensure the side panel houses all main navigation actions currently found in the header.
- Do not remove any functionality from the current header, only replace it with the new side panel.

### Requirement 2: Collapsible Side Panel Functionality
- Implement collapse/expand behavior per Figma designs.
- All sidebar menu items must remain accessible and navigable in both states.

### Requirement 3: Code Hygiene
- Audit @frontend/src/components/layout/sidebar.tsx for usage; if not used, cleanly remove it.
- New side panel code should be written from scratch using Typescript, shadcn, TailwindCSS v4, and react best practices.

## Implementation Steps (Draft v1)

1. Use the images provided with the new side panel layout to have the reference for the expected design. For both, collapsed and expanded states.
2. Audit the current usage of the existing sidebar component, remove if unused.
3. Review the header component to map current navigation structure.
4. Create a new SidePanel component according to the Figma design (collapsed and expanded).
5. Replace the header/top navigation in the main layout with the new SidePanel.
6. Migrate navigation actions, links, and visual cues from header to SidePanel.
7. Implement collapse/expand functionality and ensure accessibility.
8. Ensure styling matches the new Figma designs in the images provided and is responsive.

## Files to Modify (Initial List)

- frontend/src/components/layout/header.tsx (deprecate, only the side panel will be used)
- frontend/src/components/layout/sidebar.tsx (remove if unused)
- frontend/src/components/layout/sidepanel.tsx (create new)
- frontend/src/app/layout.tsx and all other main layout files that might need to be changed to accommodate the new side panel.

## Testing Considerations

- Verify navigation works as expected in both collapsed and expanded side panel states.
- Check for visual consistency and responsiveness across all screen sizes.
- Ensure accessibility: keyboard navigation and ARIA attributes for panel toggle.

### Error Handling

- Handle missing navigation items gracefully.
- Ensure unexpected panel state issues (e.g. stuck collapsed/expanded) revert to a safe default.

---

🤖 Next: Analyze the current layout and header components, and read the Figma spec to further detail navigation requirements and states for the plan phase.
