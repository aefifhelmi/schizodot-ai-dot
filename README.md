# schizodot-ai-dot
AI-powered Digital Observation Therapy for Individuals with Schizophrenia

## 🧭 Git Workflow (Quick Guide)

We use a **2-branch workflow** for **SchizoDot AI-Dot**:

-   `main` &rarr; Stable, production-ready code.
-   `dev` &rarr; Active development (everyone works here).

### 👩‍💻 Daily Development Flow

Follow these steps for all feature development, fixes, and updates:

| Step | Command | Description |
| :--- | :--- | :--- |
| **1. Start on `dev`** | `git checkout dev` | Ensure you are on the correct branch. |
| **2. Sync (Pull)** | `git pull origin dev` | Get the latest changes from others **before** you start working. |
| **3. Develop & Commit** | **1.** `git add .`<br>**2.** `git commit -m "feat: implemented <feature name>"` | Make your local changes, stage them, and create a descriptive commit. |
| **4. Push Changes** | `git push origin dev` | Send your committed changes to the shared `dev` branch. |

### 💡 Good Practices

* **Sync Often:** Before you start each day, and before you push, **always** run `git pull origin dev`.
* **Commit Messages:** Use clear, descriptive commit types: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`.
* **Test:** Always test your code locally before pushing it to `dev`.
* **Never** work directly on the `main` branch.

### 🔀 Merging to Main

* **Only the Project Lead (Developer 3)** is responsible for merging `dev` &rarr; `main`.
* This merge is only performed when the `dev` branch is stable and represents a new **demo-ready** version.

### 📦 Example Workflow Summary

```bash
# 1. Switch to the development branch
git checkout dev

# 2. Pull the latest updates from the remote 'dev'
git pull origin dev

# (Work on your code here)

# 3. Stage and commit your changes
git add .
git commit -m "feat: added emotion detection endpoint"

# 4. Push your local changes to the remote 'dev'
git push origin dev

```

---

Reminder: Keep main clean. Think of main as "demo-ready" — everything else happens in dev.


