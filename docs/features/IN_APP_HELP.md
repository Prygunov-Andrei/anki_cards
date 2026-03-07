# In-App Contextual Help

## Overview

Every main page has a `?` button (bottom-right corner) that opens a slide-out help panel with localized instructions, steps, and tips.

## Component

**`frontend/src/components/PageHelpButton.tsx`**

Props: `pageKey` - one of: `create`, `words`, `decks`, `training`, `categories`, `profile`, `forgettingCurve`

### Behavior

- Fixed button in bottom-right corner with `HelpCircle` icon
- First visit: pulsing blue dot indicator
- Click: opens Sheet with numbered steps + tips
- "Don't show again" dismisses permanently (per page, stored in localStorage)
- Fully localized across all 8 languages

### localStorage Keys

- `help_visited_{pageKey}` - tracks if user has seen help (removes pulse)
- `help_dismissed_{pageKey}` - hides the button entirely

## Translations

Help content is in the `help` section of each locale file:

```typescript
help: {
  tipsTitle: string;
  dontShowAgain: string;
  [pageKey]: {
    title: string;
    steps: string[];
    tips: string[];
  };
}
```

## Pages with Help

| Page | pageKey | File |
|------|---------|------|
| Create (Main) | `create` | MainPage.tsx |
| Words | `words` | WordsPage.tsx |
| Decks | `decks` | DecksPage.tsx |
| Training | `training` | TrainingDashboardPage.tsx |
| Categories | `categories` | CategoriesPage.tsx |
| Profile | `profile` | ProfilePage.tsx |
| Forgetting Curve | `forgettingCurve` | ForgettingCurvePage.tsx |
