# TEST PLAN - Audit Fixes & New Features
**Date:** January 28, 2026
**Tester:** AI QA Lead

---

## 1. ABOUT PAGE (/about)

### Feature Scope
- Static page with editor info, mission, values, team section
- Links to other pages

### Success Criteria
- Page loads without errors
- All sections render correctly
- Navigation works
- Responsive on mobile

### Test Cases
| Test | Steps | Expected | Status |
|------|-------|----------|--------|
| Page load | Navigate to /about | 200 OK, renders fully | PENDING |
| Hero section | Check hero text | "About Restaurants Quezon City" visible | PENDING |
| Editor section | Check author info | "Zachary Siecinski" visible | PENDING |
| Navigation links | Click "Home" link | Returns to homepage | PENDING |
| Mobile responsive | Resize to 375px | Layout stacks correctly | PENDING |

---

## 2. HOW WE RATE PAGE (/how-we-rate)

### Feature Scope
- Methodology page explaining rating system
- Senior-focused criteria section

### Success Criteria
- Page loads correctly
- Rating scale displays properly
- All criteria sections visible

### Test Cases
| Test | Steps | Expected | Status |
|------|-------|----------|--------|
| Page load | Navigate to /how-we-rate | 200 OK | PENDING |
| Rating scale | Check 5-star display | Stars render correctly | PENDING |
| Senior criteria | Check senior section | "Senior-Focused Approach" visible | PENDING |
| Footer links | Click "How We Rate" | Stays on page | PENDING |

---

## 3. SUBSCRIBE PAGE (/subscribe)

### Feature Scope
- Newsletter signup landing page
- Beehiv form integration

### Success Criteria
- Page loads
- Form renders
- Submit button works
- Beehiv URL is correct

### Test Cases
| Test | Steps | Expected | Status |
|------|-------|----------|--------|
| Page load | Navigate to /subscribe | 200 OK | PENDING |
| Form present | Check for email input | Input field exists | PENDING |
| Submit button | Check button | "Subscribe Now" button visible | PENDING |
| Form action | Check form action | Points to Beehiv URL | PENDING |
| Stats section | Check open rate | "32%" displayed | PENDING |

---

## 4. SENIOR-FRIENDLY PAGE (/senior-friendly)

### Feature Scope
- Hub page for senior-friendly restaurants
- Criteria section + restaurant cards + area guides

### Success Criteria
- Page loads
- All sections render
- Links to restaurants work

### Test Cases
| Test | Steps | Expected | Status |
|------|-------|----------|--------|
| Page load | Navigate to /senior-friendly | 200 OK | PENDING |
| Criteria section | Check 6 criteria | All 6 visible | PENDING |
| Restaurant cards | Check for cards | 4+ cards visible | PENDING |
| Area guide links | Click UP Town Center | Links work | PENDING |

---

## 5. NEW BLOG POSTS

### Feature Scope
- Timog blog post (30 restaurants)
- Cubao blog post (30 restaurants)

### Success Criteria
- Pages load
- Author byline present
- Schema markup valid

### Test Cases (For Each Blog)
| Test | Steps | Expected | Status |
|------|-------|----------|--------|
| Page load | Navigate to /blog/timog-restaurants-2025 | 200 OK | PENDING |
| Restaurant count | Check listing | 30 restaurants | PENDING |
| Author byline | Check bottom | "Zachary Siecinski" visible | PENDING |
| Schema valid | Check JSON-LD | Valid JSON | PENDING |
| Navigation works | Click area link | Goes to area page | PENDING |

---

## 6. BASE TEMPLATE CHANGES

### Feature Scope
- Footer updates (author, date, links)
- Navigation updates (subscribe button)

### Success Criteria
- Footer shows author on all pages
- Subscribe button appears in nav
- Date is current

### Test Cases
| Test | Steps | Expected | Status |
|------|-------|----------|--------|
| Footer author | Check home page | "Editor: Zachary Siecinski" visible | PENDING |
| Footer date | Check date | "January 28, 2026" | PENDING |
| Nav button | Check nav | "Subscribe" button present | PENDING |
| Mobile nav | Check mobile menu | Subscribe button in overlay | PENDING |

---

## 7. ROUTES (app.py)

### Feature Scope
- New routes: /how-we-rate, /subscribe, /senior-friendly

### Success Criteria
- All routes return 200
- Correct templates render

### Test Cases
| Route | Expected | Status |
|-------|----------|--------|
| /how-we-rate | Renders how-we-rate.html | PENDING |
| /subscribe | Renders subscribe.html | PENDING |
| /senior-friendly | Renders senior-friendly.html | PENDING |

---

## 8. CROSS-BROWSER CHECKS

| Browser | Status |
|---------|--------|
| Chrome (Desktop) | PENDING |
| Chrome (Mobile) | PENDING |
| Safari (Desktop) | PENDING |
| Firefox | PENDING |

---

## 9. PERFORMANCE CHECKS

| Metric | Target | Status |
|--------|--------|--------|
| Page load (/about) | < 2s | PENDING |
| Page load (/subscribe) | < 2s | PENDING |
| No JS errors | Console clean | PENDING |

---

## EXECUTION NOTES

**Testing Method:**
- Manual testing via browser inspection
- Automated curl tests for routes
- Visual regression checks (screenshot comparison not available)

**Known Limitations:**
- Cannot test actual form submission to Beehiv without live credentials
- Cannot test mobile on actual device
- Cannot test on Safari/Firefox without those browsers installed

**Risk Areas:**
- Beehiv form URL may need updating
- External links to restaurant detail pages may be broken

---

*Test execution starting...*
