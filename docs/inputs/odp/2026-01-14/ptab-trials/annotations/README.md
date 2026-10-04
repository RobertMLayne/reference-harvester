# Reader annotations for PTAB Trials captures

These notes are separate from the user-supplied documentation captures acquired on 2026-01-14. They follow the [capture handling guidance](../README.md) and [parent provenance guidance](../../README.md). The original capture files, their sample payloads, filenames and acquisition history remain the source reference.

The `.json` files listed below contain mixed documentation prose and example JSON. They are not strict JSON response files. A line number identifies the captured field-table row; each JSON pointer below is relative to the separately parsed `JSON RESPONSE SAMPLE` value, not to the whole capture file.

## Reader wording

For the ten listed rows, read the description `Time of the last ingetion` as `Time of the last ingestion`. For the four rows whose recorded field label is `lastModifiednDateTime`, read that label as `lastModifiedDateTime`. The correctly spelled field key already appears at the sample pointer in each same capture. The resulting reader row is:

```text
lastModifiedDateTime    Time of the last ingestion    Date
```

These are spelling annotations. They do not change the captured examples, validate a live endpoint, define new request parameters, change field types, or assert current API behavior. No corrected sample payload or replacement capture is produced.

## Exact capture locations and review origins

The paths are relative to the parent `ptab-trials` directory. Original review IDs are retained for traceability; these notes do not claim that GitHub threads were resolved.

| Capture and field-table line | Recorded field label | Same-capture sample pointer | Original review thread |
| --- | --- | --- | --- |
| [data.uspto.gov-apis-ptab-trials-search-decisions-400.json](../data.uspto.gov-apis-ptab-trials-search-decisions-400.json#L30), line 30 | `lastModifiednDateTime` | `/patentTrialDecisionDataBag/0/lastModifiedDateTime` | [PRRT_kwDOQ5IWYs5qRVNl](https://github.com/RobertMLayne/reference-harvester/pull/1#discussion_r2710764968) |
| [data.uspto.gov-apis-ptab-trials-search-decisions-200.json](../data.uspto.gov-apis-ptab-trials-search-decisions-200.json#L20), line 20 | `lastModifiednDateTime` | `/patentTrialDocumentDataBag/0/lastModifiedDateTime` | [PRRT_kwDOQ5IWYs5qRVNr](https://github.com/RobertMLayne/reference-harvester/pull/1#discussion_r2710764976) |
| [data.uspto.gov-apis-ptab-trials-decisions-trial-number-400.json](../data.uspto.gov-apis-ptab-trials-decisions-trial-number-400.json#L22), line 22 | `lastModifiednDateTime` | `/patentTrialDocumentDataBag/0/lastModifiedDateTime` | [PRRT_kwDOQ5IWYs5qRVN0](https://github.com/RobertMLayne/reference-harvester/pull/1#discussion_r2710764990) |
| [data.uspto.gov-apis-ptab-trials-decisions-trial-number-200.json](../data.uspto.gov-apis-ptab-trials-decisions-trial-number-200.json#L22), line 22 | `lastModifiednDateTime` | `/patentTrialDocumentDataBag/0/lastModifiedDateTime` | [PRRT_kwDOQ5IWYs5qRVOM](https://github.com/RobertMLayne/reference-harvester/pull/1#discussion_r2710765017) |
| [data.uspto.gov-apis-ptab-trials-search-documents-400.json](../data.uspto.gov-apis-ptab-trials-search-documents-400.json#L30), line 30 | `lastModifiedDateTime` | `/patentTrialDocumentDataBag/0/lastModifiedDateTime` | [PRRT_kwDOQ5IWYs5qRVOf](https://github.com/RobertMLayne/reference-harvester/pull/1#discussion_r2710765047) |
| [data.uspto.gov-apis-ptab-trials-search-documents-200.json](../data.uspto.gov-apis-ptab-trials-search-documents-200.json#L20), line 20 | `lastModifiedDateTime` | `/patentTrialDocumentDataBag/0/lastModifiedDateTime` | [PRRT_kwDOQ5IWYs5qRVOl](https://github.com/RobertMLayne/reference-harvester/pull/1#discussion_r2710765056) |
| [data.uspto.gov-apis-ptab-trials-documents-trial-number-400.json](../data.uspto.gov-apis-ptab-trials-documents-trial-number-400.json#L22), line 22 | `lastModifiedDateTime` | `/patentTrialDocumentDataBag/0/lastModifiedDateTime` | [PRRT_kwDOQ5IWYs5qRVOq](https://github.com/RobertMLayne/reference-harvester/pull/1#discussion_r2710765062) |
| [data.uspto.gov-apis-ptab-trials-documents-trial-number-200.json](../data.uspto.gov-apis-ptab-trials-documents-trial-number-200.json#L22), line 22 | `lastModifiedDateTime` | `/patentTrialDocumentDataBag/0/lastModifiedDateTime` | [PRRT_kwDOQ5IWYs5qRVOy](https://github.com/RobertMLayne/reference-harvester/pull/1#discussion_r2710765072) |
| [data.uspto.gov-apis-ptab-trials-download-proceedings-400.json](../data.uspto.gov-apis-ptab-trials-download-proceedings-400.json#L21), line 21 | `lastModifiedDateTime` | `/patentTrialProceedingDataBag/0/lastModifiedDateTime` | [PRRT_kwDOQ5IWYs5qRVO8](https://github.com/RobertMLayne/reference-harvester/pull/1#discussion_r2710765081) |
| [data.uspto.gov-apis-ptab-trials-download-proceedings-200.json](../data.uspto.gov-apis-ptab-trials-download-proceedings-200.json#L23), line 23 | `lastModifiedDateTime` | `/patentTrialProceedingDataBag/0/lastModifiedDateTime` | [PRRT_kwDOQ5IWYs5qRVPD](https://github.com/RobertMLayne/reference-harvester/pull/1#discussion_r2710765091) |

## Capture byte identities

These SHA256 values bind the annotations to the retained raw capture bytes. Git blob IDs identify the same files in source history. The annotations were prepared against source commit `c0a52cb3dab5022e59f125b46ac26afbcf4ebc49`, tree `d30872ad7b913d71df8d7fe60fbce4b73d891bc3`. A later source change requires reviewing the bindings before applying these notes.

| Capture | SHA256 of original bytes | Git blob ID |
| --- | --- | --- |
| data.uspto.gov-apis-ptab-trials-search-decisions-400.json | `db0a7a437ac0cc79fb89ee2fe1f5ec1fceb3a79bfd7b20983eb7a0e4bb6ae3cb` | `39d500ebafe39077e126ca1b0d5a43084226aebb` |
| data.uspto.gov-apis-ptab-trials-search-decisions-200.json | `2d4c5cdf06817e9e4d11f7e04556fa5f1cf2334d422515a1c1fd809428a28782` | `85b3f51adf9b8b934236a5060407369b2549319c` |
| data.uspto.gov-apis-ptab-trials-decisions-trial-number-400.json | `844f17e3ba7860f8dc17447d5bcb0aa681c6f4ba9c9190cbe9b74b524a39c4aa` | `eb07ed7cb4ab5d565b9d1a3b149d6f54e01f91fa` |
| data.uspto.gov-apis-ptab-trials-decisions-trial-number-200.json | `5c3fe420e2850b626689976aa2d1e59c6899c6f117317c38927f6b0c78b21963` | `0498c70cee039fbcc7f11ca09834b9ee938ec639` |
| data.uspto.gov-apis-ptab-trials-search-documents-400.json | `57b2aa00c097a9a0f106ce70f49e5caefeadcc77d28c4709624467233906dc60` | `cefec468883a03503f8816433f2833d466036b36` |
| data.uspto.gov-apis-ptab-trials-search-documents-200.json | `e47609523984970534c184e8c9c9fdbf3d58b5495f81a2a09bb79d61aab16bea` | `56a6d588921decc6042f601e141e5c530a340296` |
| data.uspto.gov-apis-ptab-trials-documents-trial-number-400.json | `e275a5d93ee9ad86e4c8dbe57e50a713618c184a14dae55d9ff846214f684a51` | `4f1d2ff7d26cbf4cb4d087442464b73b4e82048a` |
| data.uspto.gov-apis-ptab-trials-documents-trial-number-200.json | `630b198e5681dcc983ca857d592c3fc4a1be241dfb1acb1a7d9b078fb8a52988` | `37637084c21226f02195660aef8d4daeb7c68b6f` |
| data.uspto.gov-apis-ptab-trials-download-proceedings-400.json | `6a9b574f7313b60df30d3c63228424c4dee99c8b4fe5ba6f5513e8d9db772b5f` | `4b4c62ea0583897987b1abb476cf05885972474c` |
| data.uspto.gov-apis-ptab-trials-download-proceedings-200.json | `079485aa26f8fd7874fc2d67387c3380b529be28c38a5c95b42380ad2c8859c7` | `076e77160bee43c15d70d52b7184cedcb2df9869` |
