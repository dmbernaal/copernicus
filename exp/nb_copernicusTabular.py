
#################################################
### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
#################################################
# file to edit: dev_nb/copernicusTabular_002.ipynb

# dependencies & imports
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import numpy as np
import torch
from path import Path
from torch.utils.data import Dataset, DataLoader
from torch.autograd import Variable

import torch.nn as nn
import torch.nn.functional as F
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
torch.cuda.set_device(device)

# 1.
class TabularBunch():
    """

    NOTE: Deprecated: Need to fix multi-layered categorical filterring

    df: <pandas df>
    categorical: <df[col]>: columns which represent all categorical (discrete) variables

    This class will turn all columns but categorical & dependent into continuous variables. IF there aren't any categorical (categorical==None) then we will treat all but dependent variables as continuous.

    NB: Perform some data analysis and exploration before calling this method. For later versions we will automate this full process.

    """
    def __init__(self, df, categorical=None, dependent=None, null_thresh=0., verbose=True):
        super().__init__()
        assert dependent # needs dependent variable to work
        self.df = df.copy()
        self.categorical = categorical
        self.verbose = verbose

        # cleaning df <OPTIONAL>: removing null values from certain threshold.
        if null_thresh > 0.:
            # this will clear our categorical list: as we have to clean some columns
            self.categorical = self.purge_nulls_(null_thresh)

        # splitting X, y: Initial split | no cat/cont split
        self.Y = self.df[dependent] # all rows should have a target | dependent variable
        X = self.df.drop(columns=dependent, axis=1)

        # creating classes
        self.classes = set(y)
        ### TO DO:
        ### Create class index to class string mapping
        ### This will help with any confusion and inference level interpretation


        # filling rest of null values: will perform just incase
        X = self.fill_na_(X)

        # Splitting X into: x_cont, x_cat
        # x_cont: continuous variables
        # x_cat: categorical (discrete variables which will go into embeddings)
        if categorical is not None:
            self.X_cat = X[self.categorical].copy()
            self.X_cont = X.drop(columns=self.categorical, axis=1).copy()

        else:
            self.X_cat = None
            self.X_cont = X.copy() # do nothing: we will use this placeholder for now

        # Turning our categorical dataset: X_cat into LabelEncodings
        # This will turn cat1 -> 0, cat2 -> 1, for each cat within
        # The category columns
        self.labelencoding_()

        # Creating our embedding dictionaries
        # this will help with forming nn.Embeddings
        # and will also help with creating our datasets
        if categorical:
            self.emb_c = {n: len(col.cat.categories) for n,col in self.X_cat.items()}
            self.emb_sz = [(c, min(50, (c+1)//2)) for _,c  in self.emb_c.items()]
            self.emb_cols = self.categorical

        # our X, Y
        # this will be used to feed into our dataset class
        if self.X_cat is not None:
            if len(self.X_cont.columns) == 0:
                self.X = self.X_cat
            else:
                self.X = pd.concat([self.X_cat, self.X_cont], axis=1)
        else:
            self.X = self.X_cont

        if self.X_cat is not None and self.X_cont is not None:
            self.X_state = 'both'
        elif self.X_cat is not None and self.X_cont is None:
            self.X_state = 'catonly'
        elif self.X_cat is None and self.X_cont is not None:
            self.X_state = 'contonly'

        # Clearning our attributes: Don't need to store everything
        del self.X_cat
        del self.X_cont
        del self.categorical
        del self.verbose
        del self.df

        if verbose: print('Finished!')

    def purge_nulls_(self, null_thresh):
        """Will remove all columns with null values exceeding our threshold"""
        if self.verbose: print(f'Performing null purge. Null threshold: {null_thresh}...')

        nt = int(len(self.df) * null_thresh)

        for col in self.df.columns:
            if self.df[col].isnull().sum() > nt:
                self.df.drop(col, axis=1, inplace=True)

        cols = list(self.df.columns)
        categorical = self.categorical_left_(cols) # removing categories that are missing
        return categorical

    def fill_na_(self, X):
        """Will perform a quick processing of NA values."""
        if self.verbose: print(f'Performing NaN Replacement...')
        for col in X.columns:
            if X.dtypes[col] == "object":
                X[col] = X[col].fillna("NA")
            else:
                X[col] = X[col].fillna(0)
        return X


    def labelencoding_(self):
        if self.verbose: print(f'Performing label encoding operation. This may take a few seconds...')
        if self.X_cat is not None:
            for col in self.X_cat.columns:
                le = LabelEncoder()
                self.X_cat[col] = le.fit_transform(self.X_cat[col])
                self.X_cat[col] = self.X_cat[col].astype('category')

        # encoding our y
        le = LabelEncoder()
        self.Y = le.fit_transform(self.Y)

    def categories_left_(self, cols):
        """
        This method will return a list of all categorical columns that are left after purging our high-threshold NAs. This will simply update our list therefor not return anything.
        """
        categorical_left = pd.Series()
        for col in self.categorical:
            mask = cols == col
            masks = mask|masks
        return categories_left

    def get_train_test_(self, test_size=0.1):
        """
        This get_train_test_ method will take in a bunch object and append x_train, x_val, y_train, y_val using train_test_split from the scikit learn libray.

        This will allow for everything to be kept in a single bunch object which will feed into the Learner class and Dataset class
        """
        self.x_train, self.x_val, self.y_train, self.y_val = train_test_split(self.X,self.Y, test_size=test_size, random_state=42)

# 1b.
class AutoTabularBunch():
    """
    
    df: <pandas df>
    categorical: <df[col]>: columns which represent all categorical (discrete) variables
    purge_: <string | condition>: This will determine how to handle null values. smart: will fill na with approipriate values using a smart fill algorithm (coming soon)
        To feed a data into our Learner object (tabularlearner | NN) we cannot feed NaNs
    
    This class will turn all columns but categorical & dependent into continuous variables. IF there aren't any categorical (categorical==None) then we will treat all but dependent variables as continuous.
    
    NB: Perform some data analysis and exploration before calling this method. For later versions we will automate this full process.

    
    """
    def __init__(self, df, dependent=None, problem_type=None, null_thresh=.1, cat_thresh=0.9, purge_=None, verbose=True):
        super().__init__()
        # init declarations
        self.problem_type = 'classification' if problem_type is None else problem_type
        purge = 'null_thresh' if purge_ is None else purge_
        assert dependent # needs dependent variable to work
        assert self.problem_type == 'classification' or self.problem_type == 'regression'
        assert purge == 'aggressive' or purge == 'null_thresh' or purge == "smart"
        self.df = df.copy()
        self.verbose = verbose
        self.dependent = dependent
        
        # cleaning df <OPTIONAL>: removing null values from certain threshold.
        if purge == 'null_thresh':
            if null_thresh > 0.:
                # this will clear our categorical list: as we have to clean some columns
                self.purge_nulls_(null_thresh)
                
                if self.df[self.dependent].isnull().any():
                    raise ValueError(f'{self.dependent} column seems to have some missing values or NaN values. This will cause an error when training the model. Suggestion: Use aggressive purge_ type or pre-process the data to have no-nan values on this specific column')
        elif purge == 'aggressive':                        
            if verbose:
                print('Purging all rows with any null values: this is necessary for training otherwise use smart purge')
            mask = self.df[dependent].isnull()
            self.df = self.df[mask==False]
        elif purge == "smart":
            print('coming soon: This will fillna with appropriate values')
            

        # splitting X, y: Initial split | no cat/cont split
        self.Y = self.df[dependent] # all rows should have a target | dependent variable
        X = self.df.drop(columns=dependent, axis=1)
        
        # Grabbing categorical and setting as 'category' object time
        self.categorical = self.set_categorical(cat_thresh, X)
            
        # creating classes
        self.classes = set(self.Y)
        self.nc = len(self.classes)
        ### TO DO:
        ### Create class index to class string mapping
        ### This will help with any confusion and inference level interpretation

        
        # filling rest of null values: will perform just incase
        X = self.fill_na_(X)
            
        # Splitting X into: x_cont, x_cat
        # x_cont: continuous variables
        # x_cat: categorical (discrete variables which will go into embeddings)
        if self.categorical is not None: 
            self.X_cat = X[self.categorical].copy()
            self.X_cont = X.drop(columns=self.categorical, axis=1).copy()
            self.n_cont = len(self.X_cont.columns)
            
        else:
            self.X_cat = pd.DataFrame([])
            self.X_cont = X.copy() # do nothing: we will use this placeholder for now
            self.n_cont = None
            
        # Turning our categorical dataset: X_cat into LabelEncodings
        # This will turn cat1 -> 0, cat2 -> 1, for each cat within
        # The category columns
        self.labelencoding_()
                
        # Creating our embedding dictionaries
        # this will help with forming nn.Embeddings
        # and will also help with creating our datasets
        if self.categorical is not None:
            self.emb_c = {n: len(col.cat.categories) for n,col in self.X_cat.items()}
            self.emb_sz = [(c, min(50, (c+1)//2)) for _,c  in self.emb_c.items()]
            self.emb_cols = self.categorical
        
        # our X, Y 
        # this will be used to feed into our dataset class
        if self.X_cat is not None:
            if len(self.X_cont.columns) == 0:
                self.X = self.X_cat
            else:
                self.X = pd.concat([self.X_cat, self.X_cont], axis=1)
        else:
            self.X = self.X_cont
        
#         if self.X_cat is not None and self.X_cont is not None:
#             self.X_state = 'both'
#         elif self.X_cat is not None and self.X_cont is None:
#             self.X_state = 'catonly'
#         elif self.X_cat is None and self.X_cont is not None:
#             self.X_state = 'contonly'

        if self.X_cat.size and self.X_cont.size:
            self.X_state = 'both'
        elif self.X_cat.size and not self.X_cont.size:
            self.X_state = 'catonly'
        elif not self.X_cat.size and self.X_cont.size:
            self.X_state = 'contonly'
        
        # Clearing our attributes: Don't need to store everything
        del self.X_cat
        del self.X_cont
        del self.categorical
        del self.verbose
        del self.df
        
        if verbose: print('Finished!')
            
    def purge_nulls_(self, null_thresh):
        """Will remove all columns with null values exceeding our threshold"""
        if self.verbose: print(f'Performing null purge. Null threshold: {null_thresh}...')
        
        nt = int(len(self.df) * null_thresh)
        
        for col in self.df.columns:
            if self.df[col].isnull().sum() > nt and col != self.dependent:
                self.df.drop(col, axis=1, inplace=True)
                
    def fill_na_(self, X):
        """Will perform a quick processing of NA values."""
        if self.verbose: print(f'Performing NaN Replacement...')
        for col in X.columns:
            if X.dtypes[col] == "object":
                X[col] = X[col].fillna("NA")
            else:
                X[col] = X[col].fillna(0)
        return X
    
    def set_categorical(self, cat_thresh, X):
        """
        Will create our categorical columns based on our cat algorithm. This is the core of AutoTabularBunch. For messy datasets this may not work well and will require the use of TabularBunch
        """
        assert cat_thresh < 1. and cat_thresh > 0.
        cats_mask = ((X.nunique() < int(len(X) * cat_thresh)) & (X.dtypes == "object")) | (X.dtypes == 'object')
        categorical = [cat for cat, b in cats_mask.items() if b]
        
        if len(categorical) == 0:
            categorical = None # purely continuous variables
        return categorical
        
    
    def labelencoding_(self):
        if self.verbose: print(f'Performing label encoding operation. This may take a few seconds...')
        if self.X_cat is not None:
            for col in self.X_cat.columns:
                le = LabelEncoder()
                self.X_cat[col] = le.fit_transform(self.X_cat[col])
                self.X_cat[col] = self.X_cat[col].astype('category')
        
        # encoding our y if classification
        if self.problem_type == 'classification':
            le = LabelEncoder()
            self.Y = le.fit_transform(self.Y)
    
    def get_train_test_(self, test_size=0.1):
        """
        This get_train_test_ method will take in a bunch object and append x_train, x_val, y_train, y_val using train_test_split from the scikit learn libray. 

        This will allow for everything to be kept in a single bunch object which will feed into the Learner class and Dataset class
        """
        self.x_train, self.x_val, self.y_train, self.y_val = train_test_split(self.X,self.Y, test_size=test_size, random_state=42)

# helper function to return categorical variables
def get_categorical_(dependent, df):
    """
    Helper function to return categorical variables
    TO DO: Need to make this more dynamic, what if there are continuos variables? At the moment this function will turn all but the dependent variable as categorical variables
    """
    return list(df.columns[df.columns != dependent])

# 2.
# tabular dataset class
class TabularDataset(Dataset):
    def __init__(self, tabularbunch, ds_type='train'):
        """
        This will be our main working dataset class. We will inherit from the Dataset class provided by PyTorch which will allow use to iterate through batches appropriateley when pushed to DataLoaders
        
        If there are both cat & cont variables, this will simply create a split X1, X2 respectively. 
        """
        if ds_type == 'train':
            X = tabularbunch.x_train
            Y = tabularbunch.y_train
        else:
            X = tabularbunch.x_val
            Y = tabularbunch.y_val

        self.X_state = tabularbunch.X_state
        
        # initial split
        # we will split cat & cont variables | IF cont or cat doesn't exist
        # this will just create a single X dataset]
        if self.X_state == 'both':
            self.X1 = X.loc[:,tabularbunch.emb_cols].copy().values.astype(np.int64)
            self.X2 = X.drop(columns=tabularbunch.emb_cols).copy().values.astype(np.float32)
        elif self.X_state == 'catonly':
            self.X1 = X.copy().values.astype(np.int64)
        elif self.X_state == 'contonly':
            self.X2 = X.copy().values.astype(np.float32)
        
        if tabularbunch.problem_type == 'classification':
            if isinstance(Y, pd.Series):
                self.y = Y.values.astype(np.int64)
            else:
                self.y = Y # already int value
        elif tabularbunch.problem_type == 'regression':
            if isinstance(Y, pd.Series):
                self.y = Y.values.astype(np.float32)
            else:
                self.y = Y.astype(np.float32) # convert to float32
        
        # NORMALIZING CONT Dataset | if it exist
        if self.X_state == 'contonly' or self.X_state == 'both':
            self.X2 = (self.X2 - self.X2.mean()) / self.X2.std()
        
    def __len__(self): return len(self.y)
    def __getitem__(self, idx):
        """
        Will iterate through condition: If X2 is not empty we will return both X1 & X2, otherwise just X1
        """
        if self.X_state == 'cat_only': return self.X1[idx], self.y[idx]
        elif self.X_state == 'cont_only': return self.X2[idx], self.y[idx]
        else: return self.X1[idx], self.X2[idx], self.y[idx]

# 3.
# A
# Creating our DataBunch class which will create data objects that will
# feed into our learner class
# this will store everything regarding our data
# and will make the entire process or creating a tabular dataloader
# much easier.
# simply put: this puts everything together in one place
### V0.1.0 ###
class TabularData():
    def __init__(self, tabularbunch, test_size:float=0.1, bs:int=64, train_shuffle:bool=True,**kwargs):
        """
        Tabular Data class will host everything associated with tabular data. This will be the main class that our Learner class will use to both train and test on.

        TO DO:
        Create save methods. The user | app, should be able to save the dataloader incase of any error. This will allow for them to load the post-processed dataset into a TabularData class which will hold both DataLoaders (train, valid)


        """
        self.tabularbunch = tabularbunch
        self.tabularbunch.get_train_test_(test_size=test_size)

        # grabbing our datasets
        train_ds, valid_ds = self.get_datasets_()

        # setting our dataloaders
        self.train_dl = DataLoader(train_ds, batch_size=bs, shuffle=train_shuffle, **kwargs)
        self.valid_dl = DataLoader(valid_ds, batch_size=bs, **kwargs)

    def get_datasets_(self):
        """
        retrieve test train split
        """
        train_ds = TabularDataset(self.tabularbunch, ds_type='train')
        valid_ds = TabularDataset(self.tabularbunch, ds_type='valid')
        return train_ds, valid_ds