import warnings
import torch
import transformers
from pathlib import Path
try:
    import colbert.modeling.colbert
    colbert.modeling.colbert.ColBERT.try_load_torch_extensions = lambda *args, **kwargs: None
except ImportError:
    pass
from ragatouille import RAGPretrainedModel

# Suppress warnings 
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
torch.set_default_device('cpu')
transformers.AdamW = torch.optim.AdamW

def build_offline_index():
    print("Loading Kinyarwanda ColBERT model (C4IR-RW/kiny-colbert-free)...")
    model = RAGPretrainedModel.from_pretrained("C4IR-RW/kiny-colbert-free")
    
    # 1. Sample of knowledge base
    knowledge_base = [
        "Ikigori ni igihingwa cy’ingenzi gikura neza mubutaka bukungahaye kandi budatunganyije amazi, ahari izuba rihagije. Abahinzi bakwiye gutera imbuto mu ntiriranywa y’ibihe by’imvura kugira ngo ibihingwa bikiri bito bibone amazi ahagije.",
        "Gukingira inka ni intambwe y'ingenzi mu kwirinda indwara zica nka Borigo, Uburenge, n'Igifuruta. Kuriha inkingo hakiri kare birahendutse kuruta kuvura amatungo yarwaye.",
        "Umuti w'imburabuturo cyangwa isuka y'ibirayi ukoreshwa mu gihe cy'imvura kugira ngo hirindwe kwandura k'ubuhinzi bw'ibirayi mu Karere ka Musanze no mu Bugesera.",
        "Ibishyimbo bikenera ubutaka bwiza n'imvura iringaniye. Guhunika ibishyimbo neza bisaba gukoresha imifuka ya PICS irinda imungu kwinjira, bityo umusaruro ntiwangirike.",
        "Indwara ya Kirabiranya y'urutoki ituma amababi aba umuhondo. Ugomba kurandura igitoki cyanduye no gusukura ibikoresho byifashishijwe.",
        "Udukoko tw'icyatsi twirabura ku myumbati dushobora kwica amababi. Ni byiza gutera imiti yagenwe na RAB mu kurwanya utwo dukoko.",
        "Mu guhinga umuceri, ifumbire ya UREA ishyirwamo mu byiciro bibiri. Icya mbere ni mu gihe cyo kubagara.",
        "Niba ubutaka busharira, abahinzi bagomba gukoresha ishwagara ingana na toni 2.5 kuri hegitari kugira ngo basubize ubutaka ubuzima.",
        "Mu gihe cy'izuba ryinshi, ni byiza gukoresha uburyo bwo kwaririra (mulching) mu mirima kugira ngo ubutaka bugumane ubuhehere."
    ]

    # 2. Structured Document IDs
    document_ids = [
        "rab-maize-001",
        "rab-cattle-001",
        "rab-potato-001",
        "rab-beans-001",
        "rab-banana-001",
        "rab-cassava-001",
        "rab-rice-001",
        "rab-soil-001",
        "rab-climate-001"
    ]

    # 3. Rich Metadata for safety and traceability(filtering)
    document_metadatas = [
        {"crop": "maize", "title": "Ibigori Guidance", "section": "Planting", "page": 1, "source": "RAB"},
        {"animal": "cattle", "title": "Inka Guidance", "section": "Vaccination", "page": 2, "source": "RAB"},
        {"crop": "potato", "title": "Ibirayi Guidance", "section": "Disease", "page": 3, "source": "RAB"},
        {"crop": "beans", "title": "Ibishyimbo Guidance", "section": "Storage", "page": 4, "source": "RAB"},
        {"crop": "banana", "title": "Urutoki Guidance", "section": "Disease", "page": 5, "source": "RAB"},
        {"crop": "cassava", "title": "Imyumbati Guidance", "section": "Pests", "page": 6, "source": "RAB"},
        {"crop": "rice", "title": "Umuceri Guidance", "section": "Fertilizer", "page": 7, "source": "RAB"},
        {"topic": "soil", "title": "Ubutaka Guidance", "section": "Acidity", "page": 8, "source": "RAB"},
        {"topic": "climate", "title": "Ikirere Guidance", "section": "Drought", "page": 9, "source": "RAB"},
    ]

    index_dir = Path("runtime/indexes")
    index_dir.mkdir(parents=True, exist_ok=True)

    print("\nBuilding ColBERT FAISS index offline...")
    index_path = model.index(
        index_name="shambaguide_kinya",
        collection=knowledge_base,
        document_ids=document_ids,
        document_metadatas=document_metadatas
    )
    
    print(f"\n Index successfully built and saved to: {index_path}")

if __name__ == "__main__":
    build_offline_index()