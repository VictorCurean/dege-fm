import yaml
import seaborn as sns
import pandas as pd
from tqdm import tqdm
import torch
import torch.optim as optim
import torch.nn as nn
from torch.utils.data.dataloader import DataLoader
import matplotlib.pyplot as plt

from sc_film_v2 import FiLMResidualModel


class FiLMModelEvaluator():

    def __init__(self, config_path):
        # load config file
        self.__read_config(config_path)

        #prepare model
        self.__prepare_model()

        #read data
        self.__read_data()

    def __read_config(self, config_path):
        with open(config_path, 'r') as file:
            try:
                self.config = yaml.safe_load(file)
            except yaml.YAMLError as exc:
                print(exc)
                raise RuntimeError(exc)

    def __prepare_model(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = FiLMResidualModel(self.config)
        self.optimizer = optim.Adam(self.model.parameters(),
                                    lr=self.config['train_params']['lr'],
                                    weight_decay=self.config['train_params']['weight_decay'])
        self.criterion = nn.MSELoss()

        self.model = self.model.to(self.device)

    def __read_data(self):

        #list of drugs to include in the training and test splot

        with open(self.config['dataset_params']['sciplex_drugs_train'], "r") as f:
            drugs_train = [line.strip() for line in f]

        with open(self.config['dataset_params']['sciplex_drugs_test'], "r") as f:
            drugs_validation = [line.strip() for line in f]

        print("Loading sciplex train dataset ...")
        sciplex_dataset_train = SciplexDatasetUnseenPerturbations(self.config['dataset_params']['sciplex_adata_path'],
                                                                  drugs_train)
        self.sciplex_loader_train = DataLoader(sciplex_dataset_train, batch_size=self.config['train_params']['batch_size'],
                                         shuffle=True,
                                         num_workers=0)

        print("Loading sciplex test dataset ...")
        sciplex_dataset_test = SciplexDatasetUnseenPerturbations(self.config['dataset_params']['sciplex_adata_path'], drugs_validation)
        self.sciplex_loader_test = DataLoader(sciplex_dataset_test, batch_size=self.config['train_params']['batch_size'],
                                         shuffle=True, num_workers=0)

    def train(self):
        print("Begin training ...")
        self.model.train()  # Set the model to training mode
        losses = []

        num_epochs = self.config['train_params']['num_epochs']
        device = self.device  # Target device (e.g., 'cuda' or 'cpu')

        iteration = 0
        every_n = 10

        for epoch in range(num_epochs):
            print(f"Epoch {epoch + 1}/{num_epochs}")

            for control_emb, drug_emb, logdose, treated_emb, meta in self.sciplex_loader_train:
                # Move tensors to the specified device
                control_emb = control_emb.to(device)
                drug_emb = drug_emb.to(device)
                logdose = logdose.to(device)
                treated_emb = treated_emb.to(device)

                # Zero the gradients
                self.optimizer.zero_grad()

                # Forward pass through the model
                output = self.model(control_emb, drug_emb, logdose)

                # Compute the loss
                loss = self.criterion(output, treated_emb)

                # Backpropagation
                loss.backward()

                # Update model parameters
                self.optimizer.step()

                # Track the loss
                losses.append(loss.item())

                iteration += 1

                if iteration % every_n == 0:
                    print("Iteration:", iteration, "Loss:", loss.item())

        self.losses_train = losses
        self.trained_model = self.model

        print("Training completed.")

    def test(self, save_path=None):
        """
        Test the FiLMResidualModel and collect results.
        """
        control_embeddings = []
        treated_embeddings = []
        model_output = []
        compounds_list = []
        doses_list = []
        cell_types_list = []

        self.trained_model.eval()  # Set the model to evaluation mode

        with torch.no_grad():  # Disable gradient computation
            for control_emb, drug_emb, logdose, treated_emb, meta in tqdm(self.sciplex_loader_test):
                # Move tensors to the specified device
                control_emb = control_emb.to(self.device)
                drug_emb = drug_emb.to(self.device)
                logdose = logdose.to(self.device)
                treated_emb = treated_emb.to(self.device)

                # Forward pass through the model
                output = self.trained_model(control_emb, drug_emb, logdose)

                # Convert tensors to lists of NumPy arrays for DataFrame compatibility
                control_emb_list = [x.cpu().numpy() for x in torch.unbind(control_emb, dim=0)]
                treated_emb_list = [x.cpu().numpy() for x in torch.unbind(treated_emb, dim=0)]
                output_list = [x.cpu().numpy() for x in torch.unbind(output, dim=0)]

                # Meta information
                compounds = meta['compound']
                doses = meta['dose']
                doses = [d.item() for d in doses]
                cell_types = meta['cell_type']

                # Append results to lists
                control_embeddings.extend(control_emb_list)
                treated_embeddings.extend(treated_emb_list)
                model_output.extend(output_list)
                compounds_list.extend(compounds)
                doses_list.extend(doses)
                cell_types_list.extend(cell_types)

        # Save results into a DataFrame
        self.test_results = pd.DataFrame({
            "ctrl_emb": control_embeddings,
            "pert_emb": treated_embeddings,
            "pred_emb": model_output,
            "compound": compounds_list,
            "dose": doses_list,
            "cell_type": cell_types_list,
        })

        print("Testing completed. Results stored in 'self.test_results'.")

        # Save to file if save_path is provided
        if save_path:
            self.save_results(save_path)

    def save_results(self, save_path):
        """
        Saves test results to a file. Supports multiple formats (CSV, JSON, Pickle).
        """
        file_extension = save_path.split('.')[-1]

        if file_extension == 'csv':
            # Convert embeddings to lists for CSV compatibility
            df_to_save = self.test_results.copy()
            df_to_save['ctrl_emb'] = df_to_save['ctrl_emb'].apply(list)
            df_to_save['pert_emb'] = df_to_save['pert_emb'].apply(list)
            df_to_save['pred_emb'] = df_to_save['pred_emb'].apply(list)
            df_to_save.to_csv(save_path, index=False)
        elif file_extension == 'json':
            # Save to JSON
            self.test_results.to_json(save_path, orient='records')
        elif file_extension == 'pkl':
            # Save to Pickle for preserving object types like tensors
            self.test_results.to_pickle(save_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

        print(f"Results saved to {save_path}.")

    def plot_training_loss(self):
        plt.figure(figsize=(8, 6))
        index_losses = list(range(len(self.losses_train)))
        sns.lineplot(x=index_losses, y=self.losses_train)
        plt.ylabel("MAE")
        plt.xlabel("Iteration")
        plt.title("Train Loss")
        plt.show()


    def get_test_results(self):
        return self.test_results


class SciplexDatasetBaseline(Dataset):
    def __init__(self, adata_file, drug_list):
        self.SEP = "_"
        self.drug_list = drug_list

        self.adata = ad.read_h5ad(adata_file)
        self.data_processed = list()
        self.__match_control_to_treated()

    def __len__(self):
        # Return the number of samples
        return len(self.data_processed)

    def __match_control_to_treated(self):
        #np.random.seed(self.seed)
        adata = self.adata

        #filter only drugs of interest
        #adata = adata[adata.obs['product_name'].isin(self.drug_list + ['Vehicle'])]

        control_A549 = adata[(adata.obs['cell_type'] == "A549") & (adata.obs['product_name'] == "Vehicle")].X
        control_K562 = adata[ (adata.obs['cell_type'] == "K562") & (adata.obs['product_name'] == "Vehicle")].X
        control_MCF7 = adata[ (adata.obs['cell_type'] == "MCF7") & (adata.obs['product_name'] == "Vehicle")].X

        data_list = list() #list of dict object

        for idx in tqdm(range(adata.n_obs)):
            cell_meta = adata.obs.iloc[idx]
            cell_emb = adata.X[idx]

            if cell_meta['product_name'] == 'Vehicle':
                continue

            if cell_meta['product_name'] not in self.drug_list:
                continue

            else:
                matched_control = None
                if cell_meta['cell_type'] == "A549":
                    control_pool = control_A549
                elif cell_meta['cell_type'] == "K562":
                    control_pool = control_K562
                elif cell_meta['cell_type'] == "MCF7":
                    control_pool = control_MCF7
                else:
                    raise ValueError(f"Unknown cell type: {cell_meta['cell_type']}")

                # Randomly select a control cell from the relevant pool
                random_row_idx = np.random.choice(control_pool.shape[0])
                matched_control = control_pool[random_row_idx]

                #get drug embedding
                drug_emb = ast.literal_eval(cell_meta['sm_embedding'])

                #natural log of dose
                dose = math.log1p(cell_meta['dose'])

                #metadata
                meta = dict()
                meta['compound'] = cell_meta['product_name']
                meta['dose'] = cell_meta['dose']
                meta['cell_type'] = cell_meta['cell_type']


                # Store the treated and matched control metadata
                data_list.append({
                    "idx": idx,
                    "treated_emb": torch.tensor(cell_emb, dtype=torch.float),
                    "matched_control_emb": torch.tensor(matched_control, dtype=torch.float),
                    "drug_emb": torch.tensor(drug_emb, dtype=torch.float),
                    "logdose": torch.tensor([dose], dtype=torch.float),
                    "meta": meta
                })
        self.data_processed = data_list

    def __getitem__(self, idx):
        val = self.data_processed[idx]

        #concatenate control, drug embedding, dose
        control_emb = val['matched_control_emb']
        drug_emb = val['drug_emb']
        logdose = val['logdose']
        treated_emb = val['treated_emb']
        meta = val['meta']

        return control_emb, drug_emb, logdose, treated_emb, meta