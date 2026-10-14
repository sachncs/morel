# How morel works

morel fills in missing item information before it ranks items. Think of it as
an assembly line:

**user activity → useful neighbours → completed features → ranked items**

You do not need to understand the paper to run the library. Start with
[Getting started](../getting-started.md). This page is for readers who want
to understand what happens inside the pipeline and which part to change.

## The pipeline in plain English

| Step | What goes in | What morel does | What comes out |
| --- | --- | --- | --- |
| 1. Build the graph | User–item interactions | Connects users to the items they touched and items that appear together | A sparse interaction graph |
| 2. Find anchors | An item with at least one known modality | Finds nearby items with comparable information | A small, relevant neighbourhood |
| 3. Connect the neighbourhood | The anchor items and the graph | Keeps the paths that connect those anchors | A connected context graph |
| 4. Encode context | Features, graph links, and missing-value markers | Reads the neighbourhood together instead of item by item | One compact context vector |
| 5. Route to a codebook | The context vector | Selects a small set of learned prototype vectors | A completed latent representation |
| 6. Complete features | The representation and the missing-value markers | Predicts the missing text, image, or other modality | A full item representation |
| 7. Rank items | Users, items, and their graph | Runs the LightGCN-style recommender | Top-K recommendations |

The important product behaviour is step 6: missing features are not silently
treated as zeros. The mask tells the model which values are unavailable, and
the graph supplies context for reconstructing them.

## What is configurable?

Every stage has a stable interface. You can swap the implementation without
rewriting the stages around it:

- **Retrieval:** BFS, anchor, ACS, MAGE, or no retrieval.
- **Encoding:** the graph transformer or an identity pass-through.
- **Routing:** dense, top-k, Gumbel, or fixed routing.
- **Codebook:** vector quantisation, Gumbel-VQ, or identity.
- **Ranking:** LightGCN, matrix factorisation, or popularity baseline.

These choices live in one frozen `Config` tree. The precedence is
`CLI → environment → YAML → defaults`, and each run records the resolved
configuration in its manifest.

## The technical version

The following terms are useful when you are reading the source or the paper:

- `U` is the sparse user–item interaction matrix.
- `M` records whether each item modality is present (`1`) or missing (`0`).
- `I = sign(UᵀU)` is the item co-occurrence graph.
- The encoder turns a connected context graph into a vector `z`.
- The router chooses codebook entries; the decoder turns the selected vector
  back into one feature vector per modality.
- The ranker propagates user and item embeddings through the interaction graph
  and scores a user–item pair with a dot product.

Training compares predictions only where a modality was deliberately masked.
At evaluation time, routing is deterministic and dropout is disabled.

## Where to go next

- Change a component: [Custom component how-to](../howto/custom-component.md)
- Change settings: [Configuration reference](../reference/config.md)
- Reproduce a run: [Reproduce an experiment](../operations/reproduce.md)
- Check paper-to-code mapping: [Fidelity report](../reference/fidelity.md)
