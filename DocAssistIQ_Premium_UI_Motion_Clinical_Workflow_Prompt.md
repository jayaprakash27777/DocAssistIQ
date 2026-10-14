# DOCASSISTIQ — COMPLETE FRONTEND SMOOTHNESS, PREMIUM MOTION & PERFORMANCE ENGINEERING

## HIGHEST-PRIORITY REQUIREMENTS — READ BEFORE IMPLEMENTING

These requirements take priority over optional animation ideas. Follow them carefully and apply them to the actual application, not just a sample screen.

1. **Keep every existing feature and every existing button.** Do not delete, hide, rename, replace, or visually discard any existing button, link, field, tab, menu item, control, page, or workflow. You may improve its appearance, alignment, accessibility, responsiveness, and feedback, but its purpose and behavior must remain intact.
2. **Every visible control must work.** Audit every button and interactive element. Confirm that it triggers its existing intended action. Fix frontend wiring defects when the intended action is clear from the current code. Do not invent a new backend capability or make a control pretend to succeed. If a control is intentionally disabled by the existing application state, keep that state honest and visually clear.
3. **Prioritize layout, alignment, information structure, and readability before decorative animation.** The interface must be aligned, organized, easy to scan, and professionally spaced before adding visual effects. Do not use animation to cover a layout problem.
4. **Give the highest visual priority to Inpatient Doctor Notes, Differential Diagnosis, and DocAssist AI's input/output interface.** Review these areas in detail, component by component and state by state. They are central workflows, not secondary screens.
5. **Preserve the current theme.** Do not introduce a black or dark theme, a theme switcher, or an unrelated visual identity. Improve the theme already present in the project.
6. **Do not change clinical meaning or the backend.** Do not change the prediction engine, model, medical reasoning, diagnosis order, confidence values, investigation output, API contract, database, or generated clinical content to make the UI look better. Do not fabricate data, diagnoses, confidence scores, loading progress, citations, or success states.
7. **Use the real project as the source of truth.** Inspect existing pages, data models, response structures, buttons, states, and styling before making changes. Do not assume a component exists if it does not. Do not invent replacement screens.
8. **Make the whole application consistent.** Shared controls, spacing, typography, borders, focus states, loading states, and motion should follow one coherent system across every existing route.
9. **Keep the UI usable even when animations are unavailable.** Content and controls must remain visible and functional if a browser does not support an advanced animation feature, JavaScript animation fails, or the user requests reduced motion.
10. **Implement, then verify.** Do not stop after writing CSS or presenting recommendations. Run the available project checks and test real interactions. Report what was actually verified and disclose anything that could not be tested.

When requirements compete, use this order: preserve functionality and clinical integrity first; improve layout and readability second; improve performance and accessibility third; add motion and decorative polish fourth.

---

## 1. YOUR ROLE

Act as a senior frontend performance engineer, premium SaaS UI/UX designer, browser-animation specialist, accessibility engineer, and full-stack software engineer.

Your task is to inspect, improve, implement, and verify a production-quality frontend experience throughout my existing DocAssistIQ application.

Do not merely propose ideas, generate sample components, or give me a tutorial. Inspect the actual repository, understand the existing implementation, and make the required changes directly to the real project.

The objective is to make DocAssistIQ feel:

- Extremely smooth and responsive.
- Premium, polished, modern, and visually satisfying.
- Seamless when navigating between pages.
- Natural when scrolling.
- Responsive to every user interaction.
- Stable, without flickering, unexpected layout shifts, or visual glitches.
- Fast on both high-end and low-end hardware.
- Consistent across desktops, laptops, tablets, and mobile devices.
- Compatible with modern browsers, with graceful fallbacks for unsupported features.
- Professional and appropriate for a medical clinical-assistance application.

The design should feel intentional and refined rather than overloaded with animations.

**Primary principle: make the application feel faster without delaying real actions, compromising usability, fabricating loading progress, or altering medical functionality.**

---

# 2. ABSOLUTE RULES — DO NOT VIOLATE THESE

### A. DO NOT TOUCH THE BACKEND

This is a frontend experience and performance upgrade.

Do not modify:

- Backend business logic.
- Disease-prediction algorithms.
- Differential-diagnosis logic.
- Investigation-prediction logic.
- Model inference or model configuration.
- AI prompts used by the prediction engine.
- Medical reasoning rules.
- Backend API endpoints.
- API request methods, URLs, payloads, or response contracts.
- Authentication or authorization logic.
- Database schemas or database contents.
- Database queries.
- Existing clinical validation rules.
- Medical calculations.
- Existing error-handling semantics.
- Server configuration or deployment architecture unless a frontend build requirement strictly necessitates a change and it is explicitly justified.

Do not replace real API responses with mock data.

Do not invent results, diagnoses, probabilities, investigation recommendations, or clinical status messages.

Do not simulate successful API responses to make animations appear smoother.

Do not modify backend files just because doing so seems convenient.

Prefer changes confined to the existing frontend, its styling, and its existing component architecture.

Before implementation, identify the frontend and backend directory boundaries. At the end, verify the Git diff and confirm that no backend files were modified.

If a frontend improvement appears to require a backend change, find a frontend-only solution wherever reasonably possible.

### B. PRESERVE THE EXISTING THEME

**Do not introduce a black theme, dark theme, or a new theme-switching system.**

Preserve the application's actual current theme.

Inspect the existing colors, backgrounds, typography, navigation, cards, borders, shadows, spacing, and design tokens before making changes.

All new elements must inherit or use the existing theme.

Examples:

- Loading skeletons must use colors that fit the current theme.
- Progress indicators must use the existing brand accent.
- Dropdowns must preserve the existing surface colors.
- Modal dialogs must preserve the existing appearance.
- Hover effects must complement current button and card colors.
- Focus indicators must remain clearly visible.
- Page transitions must not introduce black or white flashes.
- Loading overlays must not unexpectedly replace the page background.
- Navigation indicators must use the existing design language.

Do not redesign the whole website unnecessarily.

Improve the polish and consistency of the current design without removing established elements or changing its identity.

### C. PRESERVE ALL EXISTING FUNCTIONALITY

Every existing screen, feature, interaction, form, button, route, API integration, table, chart, and navigation item must continue working.

Do not:

- Remove features.
- Rename API fields.
- Change route semantics.
- Break browser back or forward navigation.
- Reset form values when it is unnecessary.
- Introduce duplicate event handlers.
- Block buttons until animations finish.
- Prevent users from scrolling during ordinary application use.
- Hide important content until an animation runs.
- Require a new animation library if existing technologies can perform the task effectively.
- replace the application's working components merely to make them animated.

Animations must be enhancement layers around the existing functionality, not replacements for it.

---

# 3. PHASE ONE — AUDIT THE ACTUAL PROJECT

Before writing code, inspect the repository.

Determine:

1. The frontend framework and version.
2. Whether the project uses React, Next.js, Vite, Vue, or another framework.
3. The existing routing library and navigation architecture.
4. The styling system: CSS, CSS Modules, Tailwind, a component library, or another approach.
5. Existing animation libraries and installed versions.
6. The existing global styles and theme variables.
7. The layout components and shared navigation.
8. Every application route and major screen.
9. Existing page-loading and API-request states.
10. Forms, buttons, tabs, dialogs, dropdowns, tooltips, tables, charts, sidebars, notifications, and scroll containers.
11. Existing responsive breakpoints.
12. Existing accessibility features.
13. Existing tests, build scripts, linting rules, and formatting conventions.
14. Any known sources of unnecessary rendering or layout instability.

Inspect the package manifest and lockfile before selecting any dependency.

Check the current Git status. Preserve pre-existing user changes and do not overwrite unrelated work.

Create an internal implementation checklist based on the actual application structure.

**Do not assume that DocAssistIQ uses a particular framework or routing library. Determine this from the repository.**

Use the existing architecture wherever possible.

If the repository already has working animations, evaluate them and improve them rather than creating competing animation systems.

---

# 4. PHASE TWO — ESTABLISH A CONSISTENT MOTION DESIGN SYSTEM

Create one coherent motion system for the entire application.

Do not assign arbitrary animation durations to individual components.

Define shared, configurable design tokens for:

- Fast interaction feedback.
- Standard component transitions.
- Page transitions.
- Modal and drawer transitions.
- Enter and exit easing.
- Hover elevation.
- Reduced-motion behavior.

Use existing CSS variables if they already serve this purpose. Otherwise, add a centralized motion-token layer compatible with the current styling architecture.

Use the following values as initial targets and adjust them if repository inspection or performance testing shows a better option.

### Motion durations

| Interaction                    | Initial target |
| ------------------------------ | -------------- |
| Button press                   | 100–140 ms     |
| Button hover                   | 120–160 ms     |
| Tooltip and small menu         | 120–160 ms     |
| Card hover                     | 140–180 ms     |
| Tabs and navigation indicators | 160–200 ms     |
| Page-content transition        | 160–220 ms     |
| Modal and side drawer          | 180–240 ms     |
| Complex layout transitions     | 200–280 ms     |

These durations are defaults, not rigid rules.

Frequently used controls should respond quickly.

Never introduce lengthy animations merely to make the application look sophisticated.

### Easing

Use a small, consistent set of easing functions.

A suitable starting point is:

- Entering elements: `cubic-bezier(0.16, 1, 0.3, 1)`
- Leaving elements: `cubic-bezier(0.7, 0, 0.84, 0)`
- General interactions: `cubic-bezier(0.2, 0, 0, 1)`

Movement should feel natural and restrained.

Avoid excessive bounce, overshoot, elastic movement, and exaggerated zoom effects in ordinary clinical workflows.

### Technical rule

Prefer efficient transitions involving:

- `transform`
- `opacity`

Animate other properties only when there is a clear design reason and the performance implications have been evaluated.

Avoid blanket rules such as:

`transition: all 400ms ease;`

Do not apply `will-change` indiscriminately to every element.

Create a reusable motion system rather than scattering unrelated animation rules throughout the project.

---

# 5. PHASE THREE — IMPLEMENT SMOOTH PAGE-TO-PAGE NAVIGATION

This is one of the highest-priority requirements.

Make navigation feel seamless across all existing DocAssistIQ routes.

Audit every main navigation route, sidebar item, navigation link, and relevant internal page transition.

### Desired behavior

When a user navigates to another page:

1. The navigation action receives immediate feedback.
2. The existing page transitions without an abrupt visual flash.
3. The incoming page appears with a subtle fade and, where appropriate, a very small vertical translation.
4. The current theme remains consistent throughout the transition.
5. The new page becomes interactive without unnecessarily waiting for the animation to finish.
6. Actual content loading continues according to the existing application logic.
7. Navigation does not produce duplicate requests or unnecessary component remounts.

Use subtle transitions. For example, incoming content may start at approximately `4px` below its final position and fade into place over approximately 180 ms.

Do not animate the entire application excessively.

### Router integration

Integrate transitions with the routing system that already exists.

If the project uses React Router, use an approach compatible with its actual version and current route architecture.

If it uses Next.js, follow the conventions of the existing router and rendering architecture.

If it uses another framework, use its appropriate navigation lifecycle.

Do not replace the router.

Do not introduce a new routing abstraction merely to animate page changes.

### Native View Transitions

Evaluate the native View Transitions API where it provides a useful enhancement.

Requirements:

- Feature-detect API availability.
- Use it only for appropriate navigation or state changes.
- Provide a functional fallback when the API is unavailable.
- Avoid conflicting transitions between the native API and a JavaScript animation library.
- Account for interrupted navigation and rapid consecutive clicks.
- Avoid unnecessary full-page snapshot animations.
- Keep links and controls responsive.
- Do not introduce a black flash, incorrect background, or visual flicker.
- Follow the application's existing routing and rendering model.

Do not make support for this API a requirement for the application to function.

If another animation solution already exists and is a better fit, use the existing solution.

### Prevent common transition bugs

Explicitly check for:

- White or black flashes between routes.
- Double animations.
- Duplicate API requests.
- Frozen interfaces.
- Old page content reappearing.
- Animation remnants remaining on screen.
- Incorrect z-index ordering.
- Page content appearing underneath fixed navigation.
- Unintended horizontal overflow.
- Input values being lost.
- Focus moving to an unexpected location.
- Scroll position resetting when it should be restored.
- Animations restarting on every unrelated component update.

Do not place a mandatory animation delay before route changes.

---

# 6. PHASE FOUR — MAKE SCROLLING FEEL NATURAL AND SMOOTH

Implement a complete scrolling strategy for the application.

The objective is natural, responsive scrolling rather than artificially slow scrolling.

## A. Native wheel, touch, and trackpad scrolling

Preserve native browser scrolling behavior.

Do not globally intercept wheel, touch, or trackpad events.

Do not implement a JavaScript smooth-scrolling loop for ordinary page scrolling.

Avoid replacing native scrolling with a library unless the project already has a compelling, tested reason to do so.

The application should remain comfortable to use with:

- A mouse wheel.
- A laptop touchpad.
- A touchscreen.
- Keyboard navigation.
- A browser scrollbar.
- A high-refresh-rate display.

Do not force a custom scroll speed on different hardware.

Do not make users fight against their normal scrolling gestures.

## B. Smooth in-page navigation

Use native CSS smooth scrolling for appropriate programmatic navigation, including:

- Table-of-contents links.
- In-page section links.
- Navigation to a results section.
- Scrolling to a specific form section when appropriate.
- Deliberate scroll-to-top controls.

Use smooth scrolling only when it improves the interaction.

Do not force long animated journeys across the page.

Honor reduced-motion preferences.

## C. Route scroll restoration

Implement correct scroll-position management.

When the user opens a new primary application route, use the behavior that makes sense for the existing navigation architecture.

When the user uses browser Back or Forward, preserve or restore the expected previous scroll position.

When the user switches between tabs or filters within the same screen, do not unexpectedly return them to the top.

When the user opens a modal or dropdown, do not reset the underlying page's scroll position.

When the user returns to a previously opened medical record or results page, preserve existing useful state where the application architecture allows it.

Do not introduce unnecessary global scroll resets.

## D. Long clinical pages

Pay special attention to screens containing:

- Medical notes.
- Long patient timelines.
- Prediction results.
- Investigation tables.
- Differential diagnoses.
- Discharge summaries.
- Clinical reports.
- Long forms.
- Detailed evidence panels.

Avoid scroll hijacking, exaggerated parallax, or scroll-triggered animations that make medical information difficult to read.

Important clinical information must remain visible and accessible even if optional animations fail.

## E. Scroll-triggered and scroll-driven effects

Use CSS-based scroll-driven or scroll-triggered animation capabilities only where they provide a clear benefit.

Suitable examples include:

- A subtle reading-progress indicator.
- Gentle reveals on appropriate noncritical content sections.
- Small decorative elements whose animation does not distract from clinical information.

Do not animate every paragraph or every row of a clinical table as it enters the viewport.

Do not require JavaScript scroll listeners that continuously process every scroll event when a simpler browser-native solution is appropriate.

Use feature detection and graceful fallbacks.

Unsupported browsers must still display all content normally.

---

# 7. PHASE FIVE — IMPROVE EVERY IMPORTANT INTERACTION

Audit all existing interactive components throughout the project and improve their feedback consistently.

## A. Buttons

Implement:

- Immediate pressed-state feedback.
- Subtle hover-state transitions on devices that support hover.
- Existing brand-consistent background and border transitions.
- Clear keyboard-focus states.
- Disabled states that are visually distinct.
- Real loading states for asynchronous actions.

A subtle `scale(0.985)` pressed state may be appropriate for selected buttons.

Do not use hover movement on every mobile interaction.

Do not animate a disabled button as though it is available.

Do not delay the actual button action until its animation completes.

## B. Cards and panels

For interactive cards:

- Add subtle hover elevation.
- Use restrained border or surface changes.
- Preserve the original layout dimensions.
- Avoid unnecessary shadows or expensive visual effects.
- Respect touch-device behavior.
- Preserve existing text and content.

Do not make every informational card look clickable if it is not interactive.

## C. Sidebar and navigation

Improve:

- Active-navigation indicators.
- Hover feedback.
- Icon alignment.
- Selected states.
- Expandable navigation groups.
- Collapsed sidebar transitions, if the application supports a collapsed mode.

A shared active indicator can move smoothly between selected navigation items.

Use a shared-element animation only when it is compatible with the existing component structure.

The navigation must remain usable without animation.

## D. Tabs

Add subtle active-state transitions.

Where suitable, animate the active underline or background indicator between tabs.

Do not animate unrelated content or reset the selected tab unexpectedly.

Preserve existing tab behavior and data state.

## E. Dropdowns and tooltips

Use restrained entrance and exit effects.

A small fade combined with approximately `3–4px` of vertical movement is sufficient for most menus.

Ensure that:

- Menus remain aligned with their triggers.
- Menus do not flicker when crossing a pointer boundary.
- Focus and keyboard navigation remain functional.
- Tooltips do not obscure important clinical data.
- Menus close according to the existing interaction rules.

## F. Dialogs and modals

Implement a consistent motion pattern.

For example:

- Fade in the backdrop.
- Fade and slightly move the dialog into place.
- Keep the movement subtle.
- Reverse the effect on closing.

Do not allow an exit animation to leave an invisible modal intercepting pointer events or keyboard focus.

Preserve focus management, Escape-key behavior, accessibility attributes, and the existing modal business logic.

## G. Drawers and expandable side panels

Use restrained horizontal movement for side drawers.

Keep background and panel stacking order correct.

Prevent unwanted horizontal scrolling.

Respect touch gestures and existing responsive layouts.

If the current application contains resizable or collapsible panels, preserve their actual behavior.

## H. Accordions and expandable sections

Use natural, restrained expansion and collapse transitions.

Avoid layout jumping and unnecessary re-rendering.

If height measurement or dynamic content makes an animation unreliable, prefer a simpler, robust transition.

Do not hide information permanently if JavaScript or an animation fails.

## I. Toasts and notifications

Where notifications already exist, make their presentation consistent.

Use a compact entrance and exit animation that respects the existing theme.

Preserve notification content, severity, duration, and dismissal rules.

Do not create a successful-operation notification unless that operation actually succeeded.

Do not change error messages to hide failures.

---

# 8. PHASE SIX — ELIMINATE LOADING FLICKER

Improve the presentation of genuine loading operations without fabricating activity.

Audit existing data-fetching states and use the application's existing request lifecycle.

## A. Route loading

If route-level data actually takes time to load, provide appropriate loading feedback.

Do not show a large spinner on every immediate navigation.

For a very short operation, avoid flashing a loading indicator that disappears almost immediately.

A delayed indicator that appears only when an operation takes longer than a short threshold may be appropriate.

Remove the indicator when the actual operation finishes.

Never add artificial request delays.

Never make navigation wait for an animation.

## B. Skeleton loading states

Use skeleton placeholders where the final content structure is predictable.

Suitable areas may include:

- Dashboard cards.
- Lists.
- Search results.
- Clinical information panels.
- Tables.
- Prediction-history views.
- Other genuinely asynchronous content.

Requirements:

- Match the final content dimensions reasonably closely.
- Use the current theme's surface and accent colors.
- Avoid bright, distracting shimmer.
- Minimize layout shifts when the real content arrives.
- Avoid animating hundreds of skeleton elements separately.
- Disable or simplify shimmer for reduced-motion users.
- Do not display skeletons over content that is already available.
- Remove the skeleton as soon as the actual data is ready.

Skeletons must be visual placeholders, not fake data.

## C. Actual AI processing

Where the existing DocAssistIQ interface calls an AI prediction or another lengthy operation, preserve the current backend workflow.

Show the existing operation's actual loading state.

Only display completion when the actual operation has completed successfully.

Never fabricate percentages or imply that the AI has finished when it has not.

Do not introduce fake diagnoses to occupy an animation.

Do not change the prediction endpoint or its response contract.

## D. Failure and timeout behavior

Ensure that loading indicators do not remain indefinitely after a failed request.

Preserve existing error-handling semantics.

Display the application's actual error or recovery state.

Avoid hiding the interface behind a permanent overlay.

Allow users to retry when the existing application supports retrying.

## E. Avoid unnecessary layout shifts

Reserve space for predictable content.

Where applicable, preserve image dimensions, card sizes, table structures, and content-panel heights.

When actual content replaces a placeholder, avoid abrupt movement wherever practical without constraining legitimately dynamic content.

---

# 9. PHASE SEVEN — OPTIONAL ADVANCED ANIMATION LIBRARY

Do not install animation libraries automatically.

First inspect which animation capabilities already exist.

If the application already uses a library capable of satisfying the requirements, reuse it.

If the application uses React and genuinely needs advanced shared-element, layout, or exit animations, evaluate the current Motion for React library.

Official documentation: [https://motion.dev/docs/react](https://motion.dev/docs/react)

Potential use cases include:

- Navigation indicators.
- Component entrance and exit transitions.
- Selected shared-element animations.
- Layout changes.
- Modal lifecycle transitions.
- Carefully selected expandable elements.

Before adding a dependency:

1. Check framework compatibility.
2. Inspect the current package manager and lockfile.
3. Verify compatibility with the installed framework version.
4. Evaluate bundle-size implications.
5. Consider whether native CSS can perform the task more efficiently.
6. Avoid duplicate animation libraries.
7. Avoid replacing working architecture solely for animation.

Do not migrate from an existing library just to use a newer library.

Do not combine Motion, native View Transitions, multiple smooth-scroll libraries, and custom animation loops indiscriminately.

Choose the smallest, most reliable solution that fits the actual application.

The application must still function if an optional advanced-animation capability is unavailable.

---

# 10. PHASE EIGHT — RESPONSIVE AND CROSS-BROWSER BEHAVIOR

DocAssistIQ should work correctly across a broad range of environments.

Test or account for:

- Chrome.
- Microsoft Edge.
- Firefox.
- Safari.
- Chromium-based browsers.
- Windows.
- macOS.
- Linux.
- Android.
- iOS and iPadOS.
- Small laptop displays.
- Large monitors.
- High-DPI screens.
- Touchscreens.
- Trackpads.
- High-refresh-rate displays.
- Low-power hardware.
- Browsers with reduced-motion preferences enabled.

Do not claim universal compatibility merely because one browser passes.

When an API or animation capability is unsupported:

- Fall back to the existing functional behavior.
- Keep the content visible.
- Preserve navigation.
- Do not introduce JavaScript errors.
- Do not show an empty page.
- Do not block interaction while waiting for an unsupported animation.

Avoid depending on experimental or browser-specific features for essential functionality.

Do not require users to install browser extensions, flags, experimental settings, or special drivers.

Do not emulate 120 FPS through a forced JavaScript animation loop.

Use the browser's normal rendering pipeline.

**The target is reliable, natural smoothness across supported environments, not identical animation behavior on every device.**

---

# 11. PHASE NINE — ACCESSIBILITY AND MEDICAL WORKFLOW USABILITY

A visually smooth application must remain usable for people who prefer reduced motion or rely on assistive technology.

Implement and verify:

### Reduced motion

Respect:

`prefers-reduced-motion: reduce`

When reduced motion is requested:

- Remove unnecessary translation and scaling.
- Disable nonessential scroll-linked effects.
- Minimize or remove page-transition animations.
- Disable continuous shimmer.
- Preserve loading feedback.
- Preserve clear state changes.
- Keep all content immediately accessible.

Do not make important content dependent on an animation finishing.

### Keyboard accessibility

Preserve visible keyboard focus.

Verify that Tab, Shift+Tab, Enter, Space, and Escape work as appropriate.

Do not remove focus outlines without providing an equally visible alternative.

### Assistive technology

Preserve existing ARIA attributes and live-region behavior.

Do not announce every animation.

Loading announcements should communicate genuine state changes.

Do not cause page transitions to produce duplicate announcements.

### Clinical content

Never animate clinical text in a way that delays access to important information.

Do not apply decorative entrance effects to every diagnosis, investigation, warning, or urgent clinical status.

Preserve text selection, copying, keyboard navigation, and readability.

Ensure that error states, critical information, and important actions remain discoverable without motion.

---

# 12. PHASE TEN — PERFORMANCE ENGINEERING

The application must not become slower as a result of its animations.

The goal is smooth rendering and fast interaction, not merely an attractive appearance.

## A. Prefer efficient animation properties

Favor `transform` and `opacity` for ordinary motion.

Avoid continuous animation of layout-triggering properties when an equivalent transform-based approach is available.

Evaluate expensive paint effects individually.

Do not assume GPU acceleration guarantees smooth performance.

## B. Avoid expensive visual effects

Do not introduce unnecessary:

- Full-screen backdrop blurs.
- Animated background gradients.
- Particle systems.
- Cursor trails.
- Continuous 3D effects.
- Large parallax scenes.
- Repeated pulsing glows.
- Excessive animated shadows.
- Hundreds of simultaneous animated elements.
- Global canvas-based effects.
- Permanent decorative animations.

The current theme should remain attractive without relying on these effects.

## C. Avoid unnecessary JavaScript work

Do not create permanent animation loops.

Do not add continuously running timers for visual effects that do not need them.

Do not repeatedly calculate element positions during ordinary scrolling.

Avoid unnecessary React state updates on every animation frame.

Use event listeners, observers, and cleanup procedures appropriately when JavaScript is necessary.

Prevent memory leaks and duplicated listeners when routes change.

## D. High-refresh-rate displays

Let the browser manage normal animation timing.

Avoid assumptions that every display operates at 60 Hz.

Avoid fixed-frame JavaScript animations.

Do not degrade higher-refresh-rate displays through unnecessary main-thread work.

## E. Low-powered systems

Avoid making elaborate animation mandatory.

Keep ordinary interaction lightweight.

Disable or simplify purely decorative effects when reduced-motion preferences apply.

Use simpler effects where complex animations would create unnecessary rendering overhead.

Do not perform unreliable user-agent detection to guess device performance.

## F. Measure real performance

Inspect actual rendering behavior where tools are available.

Use Chrome DevTools Performance tools or equivalent browser profiling tools to identify:

- Long main-thread tasks.
- Repeated layout calculations.
- Expensive paint operations.
- Dropped frames.
- Excessive JavaScript execution.
- Rendering regressions.
- Unexpected layout shifts.

Prefer real measurements over assumptions.

---

# 13. PHASE ELEVEN — VISUAL POLISH ACROSS THE ENTIRE APPLICATION

Audit all current screens, not just the dashboard.

Apply consistent interaction and motion rules wherever appropriate.

Inspect:

- Login and authentication screens, if present.
- Main dashboard.
- Sidebar.
- Header.
- Navigation menus.
- Patient or consultation workflows.
- Medical-note screens.
- Prediction forms.
- Prediction results.
- Differential-diagnosis panels.
- Investigation results.
- Search interfaces.
- History pages.
- Data tables.
- Charts.
- Forms and validation messages.
- Modals.
- Dropdowns.
- Tooltips.
- Toast notifications.
- Empty states.
- Error states.
- Loading states.
- Responsive navigation.
- Long reports and summaries.

Only modify screens and components that actually exist in the repository.

Do not invent new features simply to demonstrate an animation.

For existing components, establish predictable behavior:

- Consistent timing.
- Consistent easing.
- Consistent hover feedback.
- Consistent focus states.
- Consistent entrance and exit transitions.
- Stable dimensions.
- Appropriate responsive behavior.
- Appropriate loading feedback.

Avoid over-animating frequently used clinical workflows.

The design should feel smooth and refined during ordinary use, not like an animation showcase.

---

## 13.1 — CRITICAL DESIGN STANDARD: ALIGNMENT, STRUCTURE, HIERARCHY, AND SPACING

Treat this as a precision UI cleanup across the entire existing application. Inspect every route and major screen at normal viewing size. Correct structural problems before adding decorative effects.

### Page layout and alignment

- Establish a clear page structure using the layout patterns already present in the app: app navigation, page header, page actions, primary content, and supporting content where applicable.
- Align the left edges of related headings, labels, inputs, cards, tables, and content sections. Align right-side actions and status elements consistently. Do not allow elements that should line up to drift by arbitrary amounts.
- Use consistent content gutters, margins, padding, column gaps, and vertical spacing. Reuse existing design tokens where available; otherwise create a small consistent spacing scale rather than choosing each gap independently.
- Keep headings, subtitles, filters, action buttons, badges, cards, and data tables in a predictable order. Related controls should sit together; unrelated controls should not be crowded into the same row.
- Use a stable grid or flex layout where appropriate. Avoid positioning essential content with fragile absolute positioning.
- Avoid uneven card heights, misaligned card headers, inconsistent button heights, irregular icon placement, accidental text clipping, and inconsistent border radii.
- Maintain clear separation between the main working area and secondary information without wasting screen space.
- Prevent horizontal overflow at common desktop, laptop, tablet, and mobile widths. Tables and long clinical content must remain readable and usable on narrow screens.
- Check sticky headers, sidebars, floating actions, and scrollable panels so that they do not cover page titles, form fields, results, or clinical warnings.
- Do not resize content unpredictably to create a visual effect. Reserve space for expected loading content when practical.

### Visual hierarchy and typography

- Make the page title and primary task immediately identifiable.
- Use a deliberate hierarchy for page titles, section headings, field labels, helper text, body text, metadata, badges, and secondary actions.
- Make the most important content clear through placement, readable type size, weight, spacing, and restrained contrast—not through excessive glow, bright colors, large shadows, or animation.
- Keep body text comfortable to read. Avoid overly small clinical text, long full-width paragraphs, cramped line spacing, and excessive all-caps labels.
- Use consistent typography and line-height conventions across related screens.
- Ensure long words, medical terms, identifiers, dates, and generated content wrap safely instead of overflowing their containers.
- Keep icon style, size, stroke weight, and alignment consistent. Do not replace a recognizable icon with an unrelated one just for aesthetic reasons.
- Preserve all existing labels and content unless a frontend-only wording change is clearly needed to fix a display issue and does not alter clinical meaning.

### Surface design and restraint

- Keep surfaces clean and premium using the current theme: intentional whitespace, subtle borders, restrained shadows, and consistent corner radii.
- Give panels a clear purpose. Do not put every item inside a nested card; excessive boxes reduce clarity.
- Use color to communicate existing states and hierarchy, not as decoration. Preserve the meaning of current status colors.
- Do not add decorative charts, statistics, status badges, background illustrations, or labels that are not backed by actual application data.
- Avoid heavy blur, excessive gradients, glowing borders, constant motion, and shadows that make the page look busy or slow.
- Maintain contrast between text and its existing background. Focus indicators, disabled states, and error states must remain clearly distinguishable.

### Primary action and control placement

- Every screen should make its primary existing action easy to find without hiding secondary actions that users need.
- Keep actions near the content they affect. For example, actions for an existing note should remain clearly associated with that note; actions for the prediction form should remain associated with the form.
- Standardize button height, padding, label alignment, icon placement, and spacing based on the existing design system.
- Do not make a decorative element look like a button unless it is interactive.
- Do not hide a button simply because there is not enough space; reorganize or wrap the layout responsively while keeping the control accessible.
- Preserve confirmation dialogs and safety checks that already exist. Do not bypass them to make an interaction feel faster.

### Exact visual review procedure

For every existing route, review the screen from top to bottom. Check its initial state, populated state, loading state, empty state, error state, and responsive layout wherever those states exist. Inspect the actual rendered UI, not just the source code. Where screenshot or browser tools are available, capture and review representative desktop and narrow-screen views. Correct visible alignment, spacing, clipping, contrast, and hierarchy defects before considering the screen complete.

---

## 13.2 — HIGHEST PRIORITY SCREEN: INPATIENT DOCTOR NOTES

The Inpatient Doctor Notes workflow must receive a detailed, component-by-component UI review. Preserve the actual clinical data and existing note workflow, but improve the way information is organized, read, entered, reviewed, and acted upon.

### Page structure

- Make the inpatient note page's purpose obvious as soon as it opens.
- Use the existing patient and encounter information to establish a clear top-level context. Do not invent patient details or add fake identifiers.
- Keep the page title, available patient/encounter context, current note status, and relevant existing actions in a neat, consistently aligned header area.
- Organize note content into clearly labeled sections based on fields and information already supported by the application. Depending on what exists, these may include the presenting complaint, history of present illness, relevant history, observations or vital signs, examination, investigations, assessment, plan, treatment or progress, and follow-up.
- Do not create fictional sections with fabricated values. If the existing note is a single narrative field, render it legibly without pretending the backend provides structured sections it does not provide.
- Use spacing and dividers to communicate the relationship between sections. Avoid a wall of text, deeply nested cards, or excessive empty gaps.
- If the application already supports a timeline or multiple note entries, present entries in a clear chronological order using the actual timestamps and existing ordering rules. Do not change timestamps or reorder clinical events arbitrarily.

### Note text and formatting

- Make long notes comfortable to read, with suitable line length, line height, paragraph spacing, and consistent section headings.
- Preserve user-entered note content, including meaningful line breaks and paragraph boundaries, unless the existing application deliberately transforms it.
- Avoid collapsing a whole note into one dense paragraph when the source contains paragraphs or structured sections.
- Handle long medical terms, pasted text, bullet lists, dates, and numeric values without overflow or clipping.
- If markdown rendering is already supported, make its headings, lists, tables, and emphasis clean and consistent with the existing theme. Do not introduce unsafe raw-HTML rendering.
- Keep text selectable and copyable. Do not make clinical text part of an image or canvas.
- Ensure the page remains readable when the note is very short, very long, or contains unevenly formatted source text.

### Forms and editing workflow

- Keep every existing note field, save action, edit action, cancel action, add-note action, print/export action, and other existing control. Verify each still performs its intended action.
- Align labels, inputs, helper text, validation messages, and action buttons consistently.
- Make required fields and existing validation errors easy to identify. Preserve validation logic; do not invent new rules.
- Preserve in-progress form values during unrelated UI updates and transitions.
- Distinguish viewing from editing using the existing application state. Do not make read-only content appear editable or editable fields appear disabled.
- Provide genuine saving or loading feedback only when the existing save operation is actually pending. Show success only after the real operation succeeds, and preserve real error behavior if it fails.
- Do not clear the user's note simply because a transition, tab switch, render, or animation occurs.

### Dates, status, vitals, and clinical emphasis

- Display dates, times, note status, and vital signs consistently using values already supplied by the application.
- Do not infer missing values, silently fill gaps, or convert unknown values into normal values.
- If the application already flags abnormal observations or critical information, preserve that flag and make its existing significance easy to notice without adding a new clinical interpretation.
- Keep warnings and important information visible. Never hide them inside a hover-only effect, an unexpanded panel, a transient animation, or a low-contrast badge.
- Preserve the existing distinction between historical information, current encounter information, and newly entered information wherever the data model supports it.

### Inpatient note acceptance criteria

The note screen is not complete until its content hierarchy is easy to follow, section boundaries and controls align consistently, long notes remain readable, the layout works at narrow widths, every existing action has been checked, loading and errors remain truthful, and no clinical content or backend behavior has changed.

---

## 13.3 — HIGHEST PRIORITY SCREEN: DIFFERENTIAL DIAGNOSIS

The Differential Diagnosis screen or panel is central to DocAssistIQ. Make the actual returned results easier to compare and understand without changing the clinical reasoning or implying more certainty than the real response provides.

### Result hierarchy and ordering

- Make the existing Differential Diagnosis heading and the main results area immediately identifiable.
- Preserve the order returned by the current prediction service unless the existing frontend already has an explicit, legitimate sorting control. Do not reorder diagnoses just to make the UI look better.
- Present each returned diagnosis in a clearly separated, consistently aligned result item, card, or row that matches the existing design system and the amount of data actually available.
- Make the diagnosis name the strongest text element within its result. Keep any confidence, probability, rank, or category visually secondary but easy to locate, and display it only when the real response supplies it.
- Use a consistent layout for all results so that users can compare them without searching different parts of each card.
- Do not use visual treatment that makes a lower-ranked result appear more likely than a higher-ranked result.

### Evidence and supporting information

- If the existing response contains supporting symptoms, relevant findings, explanations, evidence, or associated investigations, display those fields with clear labels and sensible grouping.
- If the existing response contains conflicting or absent findings, display them only according to the actual API response and existing product logic. Do not generate them in the frontend.
- Separate diagnosis information from investigation recommendations, warnings, and explanatory text so that different information types are not blended together.
- Preserve actual citations, provenance, source labels, and timestamps when they are already supplied. Never invent citations, references, reasons, or clinical evidence.
- Do not add fabricated confidence bars, percentage rings, ranking badges, or severity indicators. Any visualization must be a faithful representation of the corresponding real value.
- If a numeric score is shown, format it clearly and consistently without changing its value or suggesting that it has a meaning not specified by the existing application.

### Readability and comparison

- Use a clear heading, consistent vertical rhythm, and stable alignment for diagnosis names, available scores, descriptions, and action controls.
- Make the leading result easy to identify without exaggerating its certainty or hiding the remaining differential.
- Keep longer explanations readable and collapsible only if the current UI supports an appropriate expansion pattern. Important warnings must not be hidden behind an expansion control.
- Prevent long diagnosis names, gene names, organism names, medical terminology, and descriptions from breaking the layout.
- Where a table already exists, make its columns readable and responsive. Do not force a wide table to overflow the entire page on smaller screens.
- Do not add decorative charts that distract from the actual diagnosis list.

### Loading, empty, and error states

- Use the real prediction request lifecycle to determine whether the results are loading, available, empty, or failed.
- During an actual request, keep the existing form and surrounding UI usable where appropriate and display a restrained loading state that fits the current theme.
- Show actual returned results only after they have been received.
- On failure, preserve the current error behavior and offer existing recovery or retry actions where available. Do not turn a failure into a fake result.
- Do not display false completion animations, invented percentages, mock diagnoses, or generic success states to make the screen seem active.
- Preserve current clinical disclaimer and safety information. Do not rewrite or remove it as part of visual polish.

### Differential diagnosis acceptance criteria

A user must be able to identify the diagnosis list, understand the hierarchy and available supporting data, compare results in a consistent layout, locate the existing controls, and read the complete content at desktop and narrow widths. All results must retain their original values and meaning. No backend prediction logic, ranking, API contract, or clinical interpretation may change.

---

## 13.4 — HIGHEST PRIORITY: DOCASSIST AI INPUT, CONVERSATION, AND RESPONSE RENDERING

Improve the complete DocAssist AI interface wherever it exists: the user's note or query entry area, the submitted message, the genuine loading or generation state, and the AI response. The result should look clean, calm, premium, readable, and appropriate for clinical work—not like raw unformatted text dumped into a panel.

### User input and submitted note

- Make the input area clearly recognizable and easy to use. Align its label or placeholder, text area, and existing submit/send controls consistently.
- Preserve all existing controls and their actions. Do not remove the submit button, attachment control, clear control, history control, or any other control that already exists.
- Make long pasted doctor notes readable before submission. Preserve paragraphs and line breaks where the existing input supports them.
- Ensure the text area grows or scrolls according to the current component's intended behavior. It must not grow endlessly, hide the send button, or expand beyond the viewport.
- Prevent long strings, copied reports, tables, and pasted text from causing horizontal overflow.
- Make keyboard behavior predictable. Enter and Shift+Enter must follow the existing intended behavior; do not change submission semantics without checking the current implementation.
- Preserve the submitted user's exact content unless the existing application intentionally normalizes it. Do not silently rewrite a note just to improve its appearance.

### Distinguish user content from AI output

- Make the user's submitted note or query visually distinct from the AI's answer through restrained differences in alignment, label, surface, or spacing, consistent with the current theme.
- Keep user input and AI output easy to distinguish at a glance. Do not rely on color alone.
- Avoid oversized chat bubbles, excessive decoration, large unused gaps, or a layout that makes long clinical notes difficult to read.
- Preserve the chronological order of conversation messages and the existing conversation state.
- Do not duplicate a message during rerenders, navigation, retries, or response streaming.

### Render AI replies as structured, readable content

- Do not display an entire AI reply as one dense, unbroken block if the response contains headings, paragraphs, lists, or tables.
- Use the application's current markdown or rich-text renderer if one already exists. If no renderer exists and structured markdown is genuinely returned, choose a safe, compatible rendering approach after inspecting dependencies and sanitization requirements.
- Render real headings, paragraphs, bullet lists, numbered lists, emphasis, and tables with consistent spacing and typography, when those structures are present in the actual response.
- Make long answers navigable and scannable through clear heading levels, sensible paragraph widths, and whitespace. Do not invent headings or rewrite clinical meaning purely for visual effect.
- Keep medical terminology, dosages, units, dates, identifiers, citations, and other factual strings intact. Do not silently omit, paraphrase, reorder, or alter the AI's answer during presentation.
- Tables must fit the available area. On narrow screens, use a responsive container or another safe presentation that preserves access to all cells without causing page-wide overflow.
- Code or technical text, if the existing feature returns it, should wrap or scroll inside its own container rather than breaking the entire page.
- Any HTML-capable renderer must safely handle untrusted content. Do not render raw model output as executable HTML. Preserve existing sanitization and content-security protections.
- Keep text selectable and copyable. If existing copy, export, print, or regenerate controls are present, keep them and verify their actions.
- Do not add fake citations, badges, confidence indicators, medical warnings, or data that are not part of the real reply or existing application state.

### Loading and streaming behavior

- Use the actual current request or streaming state to decide when to show an activity indicator.
- If the AI is genuinely responding, show a restrained loading indicator that matches the existing theme. Do not create an animation that suggests specific words, diagnoses, or progress before those data actually arrive.
- If token streaming already exists, present incoming text incrementally without flicker, repeated content, unstable page jumps, or resetting the user's scroll position on every token.
- If streaming does not exist, do not fake it by revealing a completed answer word by word or by generating placeholder text.
- Keep the user's input and previous messages available while a real response is being generated, according to existing application behavior.
- Do not automatically jump the user to the bottom if they have scrolled upward to read an earlier message. Auto-scroll only when the user is already near the bottom or has explicitly requested it, and preserve manual scrolling.
- When a response finishes, do not force a large page jump. Keep the final content visible and accessible.
- On real failure, show the existing error or recovery state. Do not render an empty or successful-looking answer when the request failed.

### AI response actions

- Audit every existing action around the input and response, such as Send, Stop, Retry, Copy, Clear, Export, Print, or conversation-history controls, but only if those controls exist in the actual project.
- Preserve each control and test the actual intended action. Do not leave a decorative button without a working handler.
- Keep action buttons aligned consistently and close to the content they affect without crowding the response text.
- If an action is unavailable during a genuine request, retain the existing intended disabled behavior and communicate it clearly. Do not use animation as a substitute for actual functionality.
- Do not add a new control unless it has a real, supported function and can be implemented without changing backend behavior.

### AI interface acceptance criteria

A user should be able to paste or type a long clinical note, identify what was submitted, follow the returned AI answer, read any real headings and tables clearly, copy the text, and continue the conversation without layout jumps or lost input. The input and output must remain faithful to the actual data. No frontend formatting may change clinical meaning, and no backend or model behavior may change.

---

## 13.5 — EVERY BUTTON AND FEATURE MUST BE AUDITED

Treat this as a functional preservation requirement, not merely a styling task.

- Inventory the existing buttons, links, icon buttons, menus, tabs, inputs, filters, pagination controls, modal actions, note actions, prediction actions, AI response actions, and navigation items across all routes.
- For every visible control, identify its intended action from the existing source code and current behavior.
- Improve its visual consistency without changing its meaning.
- Test that clicking or activating it still performs the intended action, that it does not trigger an unrelated action, and that repeated clicks do not cause duplicate submissions.
- Check keyboard operation and focus behavior where applicable.
- Check disabled and loading states. Disabled controls must not appear active; active controls must not be blocked by an unfinished cosmetic animation.
- Preserve all existing forms, API calls, validation, dialogs, confirmation steps, download/print actions, filters, sorting, pagination, and navigation behaviors.
- Do not remove a button because it looks redundant or does not fit the new layout. Reorganize the layout so the control remains available.
- If an existing control is visibly present but has no working behavior, inspect the repository to identify its intended purpose and repair its frontend connection when that purpose is clear and already supported. If it would require a new backend capability or its purpose cannot be established, do not fake it; report it clearly in the final audit.
- Do not claim every button works unless every existing control has been audited to the extent the test environment allows.

---

## 13.6 — RESPONSIVE LAYOUT AND RENDERING OF LONG CONTENT

Check the full UI at narrow, medium, and wide widths. Do not design only for one desktop screenshot.

- At smaller widths, rearrange columns and action groups into a logical vertical flow while preserving all controls and information.
- Make cards, dialogs, tables, forms, side panels, and AI responses fit the viewport without unintended horizontal page scrolling.
- Allow genuinely wide tables to use a contained horizontal scroller rather than stretching the entire application.
- Keep important actions reachable without forcing users to scroll through unnecessary decorative space.
- Prevent sticky headers, fixed sidebars, floating buttons, or bottom input bars from covering content.
- Check zoomed layouts and long text, not only short sample content.
- Preserve the existing application breakpoints where they work; improve them only as necessary and without creating inconsistent breakpoint rules.
- Test representative very long inpatient notes, long differential explanations, large AI replies, and long user prompts. Do not validate the layout using short placeholder text alone.
- Keep content usable with browser zoom and operating-system text scaling where the environment permits.

---

## 13.7 — FINAL VISUAL REVIEW: CHECK EVERY SCREEN, NOT JUST THE DASHBOARD

Before marking the task complete, do a final pass through every real route and its important states.

For each screen, check the following in this order:

1. **Structure:** Is the content arranged in the order a user needs?
2. **Alignment:** Do related edges, headings, form controls, cards, labels, and actions line up?
3. **Hierarchy:** Can the user identify the most important content and the primary existing action immediately?
4. **Readability:** Can all labels, paragraphs, tables, and results be read without clipping, awkward wrapping, or excessive density?
5. **Completeness:** Are all existing controls and content still present?
6. **Functionality:** Do controls perform their intended actions?
7. **Responsive behavior:** Does the layout adapt without losing controls or causing unwanted overflow?
8. **Loading and error states:** Are they truthful and visually consistent?
9. **Motion:** Are transitions subtle, consistent, and non-blocking?
10. **Performance and accessibility:** Does the screen remain usable with reduced motion and without advanced browser effects?

Fix layout and functional defects before spending time on optional decorative animation. In particular, review Inpatient Doctor Notes, Differential Diagnosis, and DocAssist AI input/response rendering more carefully than purely informational pages because these are central working areas.

---

# 14. PHASE TWELVE — AUTOMATED TESTING AND MANUAL VERIFICATION

Do not stop after implementing the styles.

Run the available checks and validate the actual application.

## A. Build verification

Run the existing frontend production build.

Run the existing linting, type checks, and relevant frontend tests.

Run any targeted tests needed for the changed components.

Do not remove or weaken existing tests to make the build pass.

Do not suppress errors merely to produce a successful build.

If a command fails, investigate and resolve regressions introduced by your changes.

Clearly distinguish pre-existing failures from new failures.

## B. Navigation verification

Check that:

- Every existing route still works.
- Navigation transitions do not duplicate requests.
- Page changes do not cause flicker.
- Rapid consecutive navigation does not break the interface.
- Browser Back and Forward continue working.
- Scroll restoration behaves correctly.
- Query-string changes do not trigger inappropriate full-page transitions.
- Forms and inputs retain the expected state.
- No animation blocks interaction.

## C. Scrolling verification

Check:

- Normal wheel scrolling.
- Trackpad scrolling.
- Touch scrolling where supported.
- Keyboard scrolling.
- In-page navigation.
- Scroll-to-top controls.
- Long tables.
- Long reports.
- Internal scroll containers.
- Browser Back and Forward restoration.
- Reduced-motion behavior.

Verify that normal scrolling has not become artificially slow.

## D. Component verification

Test representative examples of:

- Buttons.
- Cards.
- Tabs.
- Dropdowns.
- Tooltips.
- Dialogs.
- Drawers.
- Accordions.
- Loading skeletons.
- Notifications.
- Forms.
- Tables.

Look for layout jumps, stale UI states, pointer-event problems, broken focus, and interrupted transitions.

## E. Browser compatibility

Use available browser automation and browser-testing tools where practical.

At minimum, verify the actual available test environment rather than claiming all browsers were tested.

Use feature detection and check that unsupported advanced-animation APIs degrade safely.

## F. Backend protection

Inspect the final diff.

Verify that:

- No backend source files were changed.
- No API endpoints were changed.
- No request or response contracts were changed.
- No model or prediction logic was modified.
- No database code was modified.
- No dummy clinical responses were introduced.
- No medical functionality was replaced with animation logic.

If any such change was made unintentionally, revert it before finishing.

## G. Performance acceptance

Use the following established Core Web Vitals targets as reference points when suitable performance measurements can be obtained:

| Metric                          | Good target   |
| ------------------------------- | ------------- |
| Largest Contentful Paint (LCP)  | ≤ 2.5 seconds |
| Interaction to Next Paint (INP) | ≤ 200 ms      |
| Cumulative Layout Shift (CLS)   | ≤ 0.1         |

Do not claim that these targets have been achieved unless the available measurements support the claim.

Separate measured results from visual inspection and unverified expectations.

Aim for consistent, low-overhead animations without adding noticeable loading time.

---

# 15. IMPLEMENTATION PRIORITIES

Work in this order.

### Priority 1 — Safety and stability

Protect the backend, existing features, theme, APIs, and clinical workflows.

Audit the actual codebase and establish a baseline.

### Priority 2 — Global motion foundation

Create shared motion tokens and accessible defaults.

Remove conflicting animation behavior where necessary.

### Priority 3 — Scrolling and navigation

Improve natural scrolling, in-page navigation, route transitions, scroll restoration, and navigation feedback.

### Priority 4 — Loading experience

Improve genuine route and data-loading feedback, skeletons, and layout stability.

### Priority 5 — Component interactions

Improve buttons, cards, tabs, dropdowns, tooltips, dialogs, drawers, accordions, and notifications.

### Priority 6 — Advanced enhancements

Add carefully chosen shared-element transitions and scroll-driven effects only when supported by the existing architecture and justified by the user experience.

### Priority 7 — Accessibility and compatibility

Test reduced motion, keyboard interactions, responsive layouts, and fallback behavior.

### Priority 8 — Verification

Run the build, type checks, linting, tests, available browser checks, and final Git-diff audit.

Do not sacrifice correctness or responsiveness to complete lower-priority visual effects.

---

# 16. DEFINITION OF DONE

The task is complete only when the implementation has been applied to the actual project and the available validation has been performed.

The result should meet these conditions:

1. The existing application theme is preserved.
2. No dark or black theme has been introduced.
3. No backend logic has been modified.
4. No existing API contract has been changed.
5. All existing routes remain functional.
6. Route transitions are subtle and consistent.
7. Scrolling remains natural and responsive.
8. In-page navigation works appropriately.
9. Browser history and scroll restoration behave correctly.
10. Genuine loading operations provide appropriate feedback.
11. Skeletons do not introduce fabricated data or excessive layout movement.
12. Interactive components provide consistent visual feedback.
13. Animations do not prevent users from interacting with the application.
14. Reduced-motion preferences are respected.
15. Unsupported animation features have functional fallbacks.
16. The application remains usable on small and large screens.
17. Unnecessary animation dependencies have not been added.
18. No unnecessary expensive rendering effects have been introduced.
19. The frontend build and available tests pass, or any unrelated existing failures are clearly documented.
20. The final diff confirms that the backend, medical reasoning, prediction logic, and APIs remain unchanged.

Do not report success simply because code was written.

Base completion claims on the actual files changed and checks executed.

---

# 17. FINAL RESPONSE AFTER IMPLEMENTATION

After completing the code changes, provide a concise engineering report containing:

**1. Repository findings:** The actual frontend framework, routing system, and existing animation approach discovered.

**2. Files changed:** The exact frontend files modified and what each change accomplishes.

**3. Features implemented:** Navigation transitions, scrolling behavior, loading states, component interactions, accessibility, and other completed improvements.

**4. Dependencies:** Any added or updated dependencies, with a clear reason. State explicitly if none were needed.

**5. Backend protection:** Confirm the results of the final Git-diff audit.

**6. Validation:** List the actual build, lint, type-check, test, and browser-verification commands executed, along with their results.

**7. Performance:** Include measured results when available. Clearly distinguish measurements from estimates.

**8. Remaining issues:** Report anything that could not be tested or verified.

Do not give me a generic implementation plan instead of modifying the application.

Do not stop after producing example CSS.

Do not claim to have tested a browser, device, or performance metric unless the relevant test was actually performed.

Start by auditing the repository, then implement the best compatible solution across the actual application, verify it, and report the results. Give special, documented attention to alignment and content structure in Inpatient Doctor Notes, Differential Diagnosis, and DocAssist AI input/output rendering. Preserve every existing feature and button, and do not change the backend or clinical meaning.