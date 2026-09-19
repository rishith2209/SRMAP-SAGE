# Evaluation & Benchmark Guide

## Objective
To ensure zero regressions, zero hallucinations, and high retrieval fidelity when updating prompts, models, or knowledge chunking strategies.

## Benchmark Metrics
1. **Retrieval Precision & Recall**: Does the top-k retrieved chunks contain the required official policy clause?
2. **Faithfulness**: Is every statement in the generated answer supported by retrieved evidence?
3. **Hallucination Rate**: Did the model invent any dates, faculty names, cabin numbers, or percentages?
4. **Citation Accuracy**: Are returned citations valid and directly related to the answer?
5. **Fallback Correctness**: When presented with an unanswerable query, does SAGE correctly respond with the fallback message?

## Running the Benchmark
```bash
python -m src.evaluation.eval_runner --dataset data/benchmark/srmap_qa_ground_truth.json
```
