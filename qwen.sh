bash scripts/infer/run_single_model_all.sh configs/yaml/qwen_math.yaml "Qwen/Qwen2.5-Math-1.5B-Instruct" 50 "" tir,plan_solve,self_ask

CUDA_VISIBLE_DEVICES=0,1 python /mnt/bn/brench-hl-volume-v1/aigc/llm-train-playground/gpu_occupy.py