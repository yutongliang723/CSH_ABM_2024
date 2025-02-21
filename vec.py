# # from variables import vec1
# import pandas as pd
# class Vec1:
#     def __init__(self, params):
#         csv_path = params["demog_file"]
#         vec1_instance = pd.read_csv(csv_path)
#         self.phi = vec1_instance.phi
#         self.rho = vec1_instance.rho
#         self.pstar = vec1_instance.pstar
#         self.mstar = vec1_instance.mstar
#         self.mortscale = vec1_instance.mortscale[0]
#         self.mortparms = vec1_instance.mortparms
#         self.fertparm = vec1_instance.fertparm[0]
#         self.fertscale = vec1_instance.fertscale[0]
        
import pandas as pd

class Vec1:
    def __init__(self, params):
        try:
            csv_path = params["demog_file"]
            vec1_data = pd.read_csv(csv_path)
            self.phi = vec1_data['phi'] 
            self.rho = vec1_data['rho']
            self.pstar = vec1_data['pstar'] 
            self.mstar = vec1_data['mstar']
            self.mortscale = vec1_data['mortscale'].iloc[0]
            self.mortparms = vec1_data['mortparms'] 
            self.fertparm = vec1_data['fertparm'].iloc[0]  
            self.fertscale = vec1_data['fertscale'].iloc[0] 
        except KeyError as e:
            print(f"KeyError: Missing key {e} in the CSV or params.")
            raise
        except Exception as e:
            print(f"Error loading Vec1 data: {e}")
            raise