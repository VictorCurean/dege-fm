import anndata.AnnData as ad

class DataBuilder:
    def __init__(self, adatas:list[AnnData],adatas_name:list[string], split_column:string, control:string, target:string):
        self.adatas = adatas
        self.adatas_name = adatas_name
        self.split_column = split_column
        self.control = control
        self.target = target

    def set_output_directory(self, output_dir):
        self.output_dir = output_dir

    def embed(self):

