# codeowners-analyzer

Code Owners Analyzer provides data about code ownership across a repository.

## Usage

```sh
python main.py \
  --team-members <TEAM MEMBERS> \
  --min-commits 3 \
  --threshold <PERCENTAGE> \
  --since <DATE>
```

## Output

The `ownership-report.json` contains information about each file the tool has analyzed. It follows a configurable rubric to determine who "owns" a particular file in a Git project.

## Help

Send us an issue.
