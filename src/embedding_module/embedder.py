import subprocess
from abc import ABC, abstractmethod


class Embedder(ABC):

    @abstractmethod
    def generate_embeddings(self):
        pass


class UCE_Embedder(Embedder):

    def __init__(self, adata, **kwargs):
        self._validate(kwargs)

    def _validate(self, kwargs):
        try:
            self.adata_loc = kwagrs['adata_loc']
            self.model_loc = kwargs['model_loc']
            self.species = kwargs['species']
            self.nlayers = kwargs['nlayers']
            self.out_dir = kwargs['out_dir']
            self.batch_size = kwargs['batch_size']
        except KeyError:
            raise RuntimeError("Incomplete Arguments for running UCE")

    def generate_embeddings(self):
        adata_name = adata_loc.split("/")[-1].split(".")[0]
        adata_uce_name = adata_name + "_uce_adata.h5ad"

        command_1 = f'mkdir {out_dir}/temp_{adata_name}/'
        command_2 = f'accelerate launch fm-code/UCE/eval_single_anndata.py --adata_path {self.adata_loc} --dir {out_dir}/temp_{self.name}/ --species {self.species} --model_loc {self.model_loc} --batch_size {self.batch_size} --nlayers {self.nlayers}'
        command_3 = f'cp {out_dir}/temp_{adata_name}/{adata_uce_name} {out_dir}/'
        command_4 = f'rm -r {out_dir}/temp_{adata_name}/'
        try:
            subprocess.run(command_1, shell=True)
            subprocess.run(command_2, shell=True)
            subprocess.run(command_3, shell=True)
            subprocess.run(command_4, shell=True)
        except subprocess.CalledProcessError as er:
            print("Error at generating UCE embeddings")
            print(er.stderr)
        except Exception as er:
            print("Error at generating UCE embeddings")
            print(str(e))





