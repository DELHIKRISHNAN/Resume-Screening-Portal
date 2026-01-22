---
tags:
- sentence-transformers
- sentence-similarity
- feature-extraction
- dense
- generated_from_trainer
- dataset_size:3402
- loss:CosineSimilarityLoss
base_model: sentence-transformers/all-mpnet-base-v2
widget:
- source_sentence: Audiologist with 6 years experience in hearing healthcare and diagnostic
    testing. Doctor of Audiology degree with state license. Strong background in hearing
    aid fitting and cochlear implant programming. Experience with pediatric and geriatric
    populations. Skilled in hearing conservation and tinnitus management.
  sentences:
  - ' "Private Equity Analyst needed to conduct due diligence  financial modeling  and
    market research for potential investment opportunities. Strong analytical skills
    and interest in private equity are essential."'
  - Hiring web content manager for e-commerce site.
  - Speech-Language Pathologist position for rehabilitation hospital. Need speech
    pathology degree and clinical license. Must have experience with swallowing disorders
    and communication therapy. Knowledge of neurological conditions and treatment
    planning preferred.
- source_sentence: Respiratory Therapist with 4 years of experience in critical care
    and ventilator management. Certified in RRT.
  sentences:
  - Hiring a Carpenter for custom furniture and cabinetry projects.
  - Seeking a Respiratory Therapist with RRT certification and critical care experience.
  - ' "Senior Software Engineer with 5+ years of experience in Python/Django development
    and React. The ideal candidate will have strong experience with AWS services  CI/CD  and
    database optimization. Leadership experience and a passion for building scalable
    web applications are a plus."'
- source_sentence: Personal Banker with 4 years experience in retail banking services.
    Strong background in account opening and customer service. Experience with banking
    software and regulatory compliance. Skilled in product sales and financial counseling.
  sentences:
  - Hiring an Automotive Mechanic with ASE certification for vehicle repairs.
  - Legal Transcriptionist position for law firm. Need transcription experience and
    legal knowledge. Must have strong typing skills and attention to detail. Experience
    with legal documents and audio transcription preferred.
  - Branch Manager position for community bank. Need banking experience and leadership
    skills. Must have knowledge of banking operations and regulatory requirements.
    Experience with business development and staff management preferred.
- source_sentence: Web developer with WordPress and WooCommerce experience.
  sentences:
  - Seeking web developer for custom e-commerce site development using WooCommerce.
  - ' "Fashion Designer with 5 years of experience creating apparel collections from
    concept to production. Skilled in sketching  pattern making  fabric selection  and
    garment construction. Proficient in Adobe Illustrator and Photoshop. Strong portfolio."'
  - ' "Cyber Threat Hunter responsible for proactively searching for  detecting  and
    responding to advanced persistent threats within an enterprise network. Strong
    understanding of adversary tactics  techniques  and procedures (TTPs) is required."'
- source_sentence: Biomedical Engineer with 3 years of experience in medical device
    design and SolidWorks. Ensured FDA compliance.
  sentences:
  - Hiring Microgravity Agriculture Professor
  - Seeking a Biomedical Engineer with SolidWorks and medical device design experience.
  - Hiring a Structural Engineer with SAP2000 and seismic design experience.
pipeline_tag: sentence-similarity
library_name: sentence-transformers
---

# SentenceTransformer based on sentence-transformers/all-mpnet-base-v2

This is a [sentence-transformers](https://www.SBERT.net) model finetuned from [sentence-transformers/all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2). It maps sentences & paragraphs to a 768-dimensional dense vector space and can be used for semantic textual similarity, semantic search, paraphrase mining, text classification, clustering, and more.

## Model Details

### Model Description
- **Model Type:** Sentence Transformer
- **Base model:** [sentence-transformers/all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2) <!-- at revision 12e86a3c702fc3c50205a8db88f0ec7c0b6b94a0 -->
- **Maximum Sequence Length:** 384 tokens
- **Output Dimensionality:** 768 dimensions
- **Similarity Function:** Cosine Similarity
<!-- - **Training Dataset:** Unknown -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Documentation:** [Sentence Transformers Documentation](https://sbert.net)
- **Repository:** [Sentence Transformers on GitHub](https://github.com/UKPLab/sentence-transformers)
- **Hugging Face:** [Sentence Transformers on Hugging Face](https://huggingface.co/models?library=sentence-transformers)

### Full Model Architecture

```
SentenceTransformer(
  (0): Transformer({'max_seq_length': 384, 'do_lower_case': False, 'architecture': 'MPNetModel'})
  (1): Pooling({'word_embedding_dimension': 768, 'pooling_mode_cls_token': False, 'pooling_mode_mean_tokens': True, 'pooling_mode_max_tokens': False, 'pooling_mode_mean_sqrt_len_tokens': False, 'pooling_mode_weightedmean_tokens': False, 'pooling_mode_lasttoken': False, 'include_prompt': True})
  (2): Normalize()
)
```

## Usage

### Direct Usage (Sentence Transformers)

First install the Sentence Transformers library:

```bash
pip install -U sentence-transformers
```

Then you can load this model and run inference.
```python
from sentence_transformers import SentenceTransformer

# Download from the 🤗 Hub
model = SentenceTransformer("sentence_transformers_model_id")
# Run inference
sentences = [
    'Biomedical Engineer with 3 years of experience in medical device design and SolidWorks. Ensured FDA compliance.',
    'Seeking a Biomedical Engineer with SolidWorks and medical device design experience.',
    'Hiring a Structural Engineer with SAP2000 and seismic design experience.',
]
embeddings = model.encode(sentences)
print(embeddings.shape)
# [3, 768]

# Get the similarity scores for the embeddings
similarities = model.similarity(embeddings, embeddings)
print(similarities)
# tensor([[1.0000, 0.9576, 0.2967],
#         [0.9576, 1.0000, 0.2972],
#         [0.2967, 0.2972, 1.0000]])
```

<!--
### Direct Usage (Transformers)

<details><summary>Click to see the direct usage in Transformers</summary>

</details>
-->

<!--
### Downstream Usage (Sentence Transformers)

You can finetune this model on your own dataset.

<details><summary>Click to expand</summary>

</details>
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Dataset

#### Unnamed Dataset

* Size: 3,402 training samples
* Columns: <code>sentence_0</code>, <code>sentence_1</code>, and <code>label</code>
* Approximate statistics based on the first 1000 samples:
  |         | sentence_0                                                                         | sentence_1                                                                        | label                                                           |
  |:--------|:-----------------------------------------------------------------------------------|:----------------------------------------------------------------------------------|:----------------------------------------------------------------|
  | type    | string                                                                             | string                                                                            | float                                                           |
  | details | <ul><li>min: 5 tokens</li><li>mean: 26.28 tokens</li><li>max: 197 tokens</li></ul> | <ul><li>min: 5 tokens</li><li>mean: 20.6 tokens</li><li>max: 238 tokens</li></ul> | <ul><li>min: 0.0</li><li>mean: 0.74</li><li>max: 0.99</li></ul> |
* Samples:
  | sentence_0                                                                                                                                                                                                                                              | sentence_1                                                                                                                                                                                                                                                              | label             |
  |:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------|
  | <code>AI Engineer with 3 years of experience in Python and deep learning. Built models for natural language processing.</code>                                                                                                                          | <code>Hiring an AI Engineer with Python and deep learning experience.</code>                                                                                                                                                                                            | <code>0.95</code> |
  | <code>Licensed practical nurse with 4 years in elder care and medication administration.</code>                                                                                                                                                         | <code>Hiring LPN for assisted living facility. Medication management required.</code>                                                                                                                                                                                   | <code>0.95</code> |
  | <code>Fashion Stylist with 4 years of experience providing personal styling services for editorial shoots, fashion campaigns, and private clients. Strong understanding of current trends, body types, and brand aesthetics. Portfolio required.</code> | <code> "Fashion Designer with 5 years of experience creating apparel collections from concept to production. Skilled in sketching  pattern making  fabric selection  and garment construction. Proficient in Adobe Illustrator and Photoshop. Strong portfolio."</code> | <code>0.5</code>  |
* Loss: [<code>CosineSimilarityLoss</code>](https://sbert.net/docs/package_reference/sentence_transformer/losses.html#cosinesimilarityloss) with these parameters:
  ```json
  {
      "loss_fct": "torch.nn.modules.loss.MSELoss"
  }
  ```

### Training Hyperparameters
#### Non-Default Hyperparameters

- `per_device_train_batch_size`: 16
- `per_device_eval_batch_size`: 16
- `num_train_epochs`: 2
- `multi_dataset_batch_sampler`: round_robin

#### All Hyperparameters
<details><summary>Click to expand</summary>

- `overwrite_output_dir`: False
- `do_predict`: False
- `eval_strategy`: no
- `prediction_loss_only`: True
- `per_device_train_batch_size`: 16
- `per_device_eval_batch_size`: 16
- `per_gpu_train_batch_size`: None
- `per_gpu_eval_batch_size`: None
- `gradient_accumulation_steps`: 1
- `eval_accumulation_steps`: None
- `torch_empty_cache_steps`: None
- `learning_rate`: 5e-05
- `weight_decay`: 0.0
- `adam_beta1`: 0.9
- `adam_beta2`: 0.999
- `adam_epsilon`: 1e-08
- `max_grad_norm`: 1
- `num_train_epochs`: 2
- `max_steps`: -1
- `lr_scheduler_type`: linear
- `lr_scheduler_kwargs`: {}
- `warmup_ratio`: 0.0
- `warmup_steps`: 0
- `log_level`: passive
- `log_level_replica`: warning
- `log_on_each_node`: True
- `logging_nan_inf_filter`: True
- `save_safetensors`: True
- `save_on_each_node`: False
- `save_only_model`: False
- `restore_callback_states_from_checkpoint`: False
- `no_cuda`: False
- `use_cpu`: False
- `use_mps_device`: False
- `seed`: 42
- `data_seed`: None
- `jit_mode_eval`: False
- `use_ipex`: False
- `bf16`: False
- `fp16`: False
- `fp16_opt_level`: O1
- `half_precision_backend`: auto
- `bf16_full_eval`: False
- `fp16_full_eval`: False
- `tf32`: None
- `local_rank`: 0
- `ddp_backend`: None
- `tpu_num_cores`: None
- `tpu_metrics_debug`: False
- `debug`: []
- `dataloader_drop_last`: False
- `dataloader_num_workers`: 0
- `dataloader_prefetch_factor`: None
- `past_index`: -1
- `disable_tqdm`: False
- `remove_unused_columns`: True
- `label_names`: None
- `load_best_model_at_end`: False
- `ignore_data_skip`: False
- `fsdp`: []
- `fsdp_min_num_params`: 0
- `fsdp_config`: {'min_num_params': 0, 'xla': False, 'xla_fsdp_v2': False, 'xla_fsdp_grad_ckpt': False}
- `fsdp_transformer_layer_cls_to_wrap`: None
- `accelerator_config`: {'split_batches': False, 'dispatch_batches': None, 'even_batches': True, 'use_seedable_sampler': True, 'non_blocking': False, 'gradient_accumulation_kwargs': None}
- `deepspeed`: None
- `label_smoothing_factor`: 0.0
- `optim`: adamw_torch
- `optim_args`: None
- `adafactor`: False
- `group_by_length`: False
- `length_column_name`: length
- `ddp_find_unused_parameters`: None
- `ddp_bucket_cap_mb`: None
- `ddp_broadcast_buffers`: False
- `dataloader_pin_memory`: True
- `dataloader_persistent_workers`: False
- `skip_memory_metrics`: True
- `use_legacy_prediction_loop`: False
- `push_to_hub`: False
- `resume_from_checkpoint`: None
- `hub_model_id`: None
- `hub_strategy`: every_save
- `hub_private_repo`: False
- `hub_always_push`: False
- `gradient_checkpointing`: False
- `gradient_checkpointing_kwargs`: None
- `include_inputs_for_metrics`: False
- `include_for_metrics`: []
- `eval_do_concat_batches`: True
- `fp16_backend`: auto
- `push_to_hub_model_id`: None
- `push_to_hub_organization`: None
- `mp_parameters`: 
- `auto_find_batch_size`: False
- `full_determinism`: False
- `torchdynamo`: None
- `ray_scope`: last
- `ddp_timeout`: 1800
- `torch_compile`: False
- `torch_compile_backend`: None
- `torch_compile_mode`: None
- `dispatch_batches`: None
- `split_batches`: None
- `include_tokens_per_second`: False
- `include_num_input_tokens_seen`: False
- `neftune_noise_alpha`: None
- `optim_target_modules`: None
- `batch_eval_metrics`: False
- `eval_on_start`: False
- `use_liger_kernel`: False
- `eval_use_gather_object`: False
- `prompts`: None
- `batch_sampler`: batch_sampler
- `multi_dataset_batch_sampler`: round_robin
- `router_mapping`: {}
- `learning_rate_mapping`: {}

</details>

### Framework Versions
- Python: 3.10.0
- Sentence Transformers: 5.0.0
- Transformers: 4.46.0
- PyTorch: 2.7.1+cpu
- Accelerate: 1.8.1
- Datasets: 4.0.0
- Tokenizers: 0.20.3

## Citation

### BibTeX

#### Sentence Transformers
```bibtex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->