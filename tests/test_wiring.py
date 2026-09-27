"""The repo's own wiring: agents point at prompts that exist, every agent is known to the guard,
the cold roles stay cold, and the knowledge bases are OKF-shaped with no broken links."""
import json
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import export_prose  # noqa: E402  (its frontmatter parser)
import guard  # noqa: E402

AGENTS = os.path.join(ROOT, ".claude", "agents")
KB = os.path.join(ROOT, "kb")
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")
COLD = {"beta-reader", "judge"}


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def agents():
    for name in sorted(os.listdir(AGENTS)):
        if name.endswith(".md"):
            fields, body = export_prose.split_frontmatter(read(os.path.join(AGENTS, name)))
            yield name[:-3], fields, body


def kb_docs():
    for dirpath, _, files in os.walk(KB):
        for name in sorted(files):
            if name.endswith(".md"):
                yield os.path.join(dirpath, name)


class AgentWiringTest(unittest.TestCase):
    def test_agents_exist(self):
        names = {name for name, _, _ in agents()}
        self.assertTrue({"planner", "writer", "beta-reader", "story-editor", "line-editor",
                         "judge"} <= names, names)

    def test_frontmatter_and_prompt(self):
        for name, fields, body in agents():
            with self.subTest(agent=name):
                self.assertEqual(fields.get("name"), name)
                for key in ("description", "tools", "model"):
                    self.assertTrue(fields.get(key), "%s has no %s" % (name, key))
                self.assertEqual(fields.get("omitClaudeMd"), "true")
                prompt = "kb/%s/prompt.md" % name
                self.assertIn(prompt, body)
                self.assertTrue(os.path.isfile(os.path.join(ROOT, prompt)), prompt)

    def test_every_agent_is_known_to_the_guard(self):
        for name, _, _ in agents():
            self.assertIn(name, guard.ROLES, "%s would fail open in tools/guard.py" % name)

    def test_cold_roles_stay_cold(self):
        for name, fields, _ in agents():
            if name in COLD:
                tools = {t.strip() for t in fields["tools"].split(",")}
                self.assertNotIn("Bash", tools, "%s must not have Bash: the guard cannot see it" % name)
                self.assertIn("read_only", guard.ROLES[name])

    def test_models(self):
        models = {name: fields["model"] for name, fields, _ in agents()}
        for name in ("planner", "writer", "story-editor"):
            self.assertEqual(models[name], "opus", name)
        for name in ("beta-reader", "line-editor"):
            self.assertEqual(models[name], "sonnet", name)
        self.assertEqual(models["judge"], "claude-opus-5")

    def test_settings_wire_the_guard(self):
        settings = json.loads(read(os.path.join(ROOT, ".claude", "settings.json")))
        commands = [h["command"] for entry in settings["hooks"]["PreToolUse"]
                    for h in entry["hooks"]]
        self.assertTrue(any("tools/guard.py" in c for c in commands))
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "tools", "guard.py")))

    def test_settings_wire_the_session_hooks(self):
        settings = json.loads(read(os.path.join(ROOT, ".claude", "settings.json")))
        for event in ("Stop", "SubagentStop", "StopFailure", "SessionEnd", "PreCompact",
                      "SessionStart", "UserPromptSubmit", "PostToolUse"):
            commands = [h["command"] for entry in settings["hooks"].get(event, [])
                        for h in entry["hooks"]]
            self.assertTrue(any("tools/session_hooks.py" in c for c in commands), event)
        self.assertIn("tools/statusline.py", settings["statusLine"]["command"])
        self.assertTrue(os.path.isfile(os.path.join(ROOT, ".claude", "skills", "handoff",
                                                    "SKILL.md")))


class KnowledgeBaseTest(unittest.TestCase):
    def test_every_doc_has_a_type(self):
        for path in kb_docs():
            if os.path.basename(path) == "index.md":
                continue
            with self.subTest(doc=os.path.relpath(path, ROOT)):
                fields, _ = export_prose.split_frontmatter(read(path))
                self.assertTrue(fields.get("type"), "OKF requires a non-empty type")

    def test_every_bundle_has_an_index_listing_its_docs(self):
        for bundle in sorted(os.listdir(KB)):
            bdir = os.path.join(KB, bundle)
            if not os.path.isdir(bdir):
                continue
            with self.subTest(bundle=bundle):
                index = os.path.join(bdir, "index.md")
                self.assertTrue(os.path.isfile(index))
                linked = set(LINK.findall(read(index)))
                for name in os.listdir(bdir):
                    if name.endswith(".md") and name != "index.md":
                        self.assertIn(name, linked, "%s/%s is not in its index" % (bundle, name))

    def test_links_resolve(self):
        for path in list(kb_docs()) + [os.path.join(ROOT, "CLAUDE.md")]:
            for target in LINK.findall(read(path)):
                if "://" in target:
                    continue
                with self.subTest(doc=os.path.relpath(path, ROOT), link=target):
                    self.assertTrue(os.path.exists(os.path.join(os.path.dirname(path), target)))

    def test_root_index_declares_okf_version(self):
        fields, _ = export_prose.split_frontmatter(read(os.path.join(KB, "index.md")))
        self.assertTrue(fields.get("okf_version"))


if __name__ == "__main__":
    unittest.main()
