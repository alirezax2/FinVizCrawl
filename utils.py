def upload_to_hf_dataset(file_path, dataset_name, token, repo_type="dataset"):
    """
    Upload a file to a Hugging Face dataset repository.
    
    Args:
        file_path (str): Path to the file to upload
        dataset_name (str): Name of the dataset in format 'username/dataset-name'
        token (str): Hugging Face API token
        repo_type (str): Repository type, defaults to 'dataset'
    """
    from huggingface_hub import HfApi
    import os

    # Initialize the Hugging Face API client
    api = HfApi()
    
    try:
        # Upload the file to the dataset repository
        api.upload_file(
            path_or_fileobj=file_path,
            path_in_repo=os.path.basename(file_path),  # Use filename as path in repo
            repo_id=dataset_name,
            repo_type=repo_type,
            token=token,
            commit_message=f"Upload {os.path.basename(file_path)}",
            commit_description=f"Automated upload of {os.path.basename(file_path)} to dataset"
        )
        print(f"Successfully uploaded {file_path} to {dataset_name}")
    except Exception as e:
        print(f"Error uploading file: {str(e)}")




def download_from_hf_dataset(file_path, dataset_name, token, repo_type="dataset"):
    """
    Download a file from a Hugging Face dataset repository.
    
    Args:
        file_path (str): Path in the repository to download from
        dataset_name (str): Name of the dataset in format 'username/dataset-name'
        token (str): Hugging Face API token
        repo_type (str): Repository type, defaults to 'dataset'
    """
    from huggingface_hub import HfApi
    import os

    # Initialize the Hugging Face API client
    api = HfApi()
    
    try:
        # Download the file from the dataset repository
        api.hf_hub_download(
            repo_id=dataset_name,
            filename=file_path,
            repo_type=repo_type,
            local_dir=".",
            token=token
        )
        print(f"Successfully downloaded {file_path} from {dataset_name}")
    except Exception as e:
        print(f"Error downloading file: {str(e)}")




def load_hf_dataset(csv_filename, token, dataset_name_input):
    """
    Load a CSV dataset from Hugging Face and return as pandas DataFrame
    
    Args:
        csv_filename (str): Name of the CSV file in the dataset
        token (str): Hugging Face authentication token
        
    Returns:
        pandas.DataFrame: DataFrame containing the dataset
    """
    from datasets import load_dataset
    
    try:
        dataset = load_dataset(dataset_name_input, 
                                data_files=csv_filename,
                                split="train",
                                token=token)
        return dataset.to_pandas()
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return None


