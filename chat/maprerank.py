from langchain.chains.combine_documents.map_rerank import MapRerankDocumentsChain
from langchain.docstore.document import Document
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union, cast


class MyMapRerankDocumentsChain(MapRerankDocumentsChain):

    def _process_results(
        self,
        docs: List[Document],
        results: Sequence[Union[str, List[str], Dict[str, str]]],
    ) -> Tuple[str, dict]:
        typed_results = cast(List[dict], results)
        sorted_res = sorted(
            zip(typed_results, docs), key=lambda x: -int(x[0][self.rank_key])
        )   
        output, document = sorted_res[0]
        extra_info = {}
        if self.metadata_keys is not None:
            for key in self.metadata_keys:
                extra_info[key] = document.metadata[key]
        if self.return_intermediate_steps:
            extra_info["intermediate_steps"] = results
        output["_doc_"] = document.page_content
        output["_doc_metadata_"] = document.metadata
        return output, extra_info
