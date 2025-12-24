# codeowners-analyzer

Code Owners Analyzer provides data about code ownership across a repository.

## Usage

```sh
python main.py \
  --team-members <TEAM MEMBERS:str> \
  --min-commits <MININUM:int> \
  --threshold <PERCENTAGE:float> \
  --since <DATE:datestr>
```

## Output

The `ownership-report.json` contains information about each file the tool has analyzed. It follows a configurable rubric to determine who "owns" a particular file in a Git project.

## Help

Send us an issue.
