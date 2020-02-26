import tensorflow as tf
from gpflow.decors import params_as_tensors
import gpflow
import math 
import numpy as np




class binned_kernel(gpflow.kernels.Kernel):
    def __init__(self, input_dim, active_dims, index_dim,variance= 10.0, lengthscales=[1,1]):
        gpflow.kernels.Kernel.__init__(self, input_dim=input_dim, active_dims=active_dims)
        self.variance = gpflow.Param(variance, transform=gpflow.transforms.positive, dtype = 'float64')
        self.Lon = 0.74
        self.Lat = 1.64
        self.lengthscale = gpflow.Param(lengthscales, transform=gpflow.transforms.positive,dtype = 'float64')
        self.variance_binned = gpflow.Param(3, transform=gpflow.transforms.positive,dtype = 'float64')
        self.index_dim = index_dim
    
    def binned_normal_correlation(self, X1_11, X2_12,agg,lengthscale):

        dist_11 = tf.reshape(X1_11, (-1, 1)) - tf.reshape(X2_12, (1, -1))+agg/2
        dist_11 = dist_11/lengthscale
        dist_12 = -tf.reshape(X1_11, (-1, 1)) + tf.reshape(X2_12, (1, -1))+agg/2
        dist_12 = dist_12/lengthscale
        pi = tf.constant(math.pi,dtype='float64')
        KK = 0.5*tf.sqrt(pi)*lengthscale*(tf.math.erf(dist_11)+tf.math.erf(dist_12))
        
        return KK
    
    def binned_normal_correlation2(self, X1_11, X2_12,agg,lengthscale):

        dist_11 = -tf.reshape(X1_11, (-1, 1)) + tf.reshape(X2_12, (1, -1))+agg/2
        dist_11 = dist_11/lengthscale
        dist_12 = tf.reshape(X1_11, (-1, 1)) - tf.reshape(X2_12, (1, -1))+agg/2
        dist_12 = dist_12/lengthscale
        pi = tf.constant(math.pi,dtype='float64')
        KK = 0.5*tf.sqrt(pi)*lengthscale*(tf.math.erf(dist_11)+tf.math.erf(dist_12))
        
        return KK


    def binned_g(self,z):
        pi = tf.constant(math.pi,dtype='float64')
        tmp = z*tf.sqrt(pi)*tf.math.erf(z)+tf.exp(-tf.square(z))
        return tmp


    def binned_correlation(self, s, t,agg,lengthscale):

        dist_1 = tf.reshape(s, (-1, 1)) - tf.reshape(t, (1, -1))+agg
        dist_1 = dist_1/lengthscale
        dist_2 = -tf.reshape(s, (-1, 1)) + tf.reshape(t, (1, -1))+agg
        dist_2 = dist_2/lengthscale
        dist_3 = tf.reshape(s, (-1, 1)) - tf.reshape(t, (1, -1))
        dist_3 = dist_3/lengthscale
        dist_4 = -tf.reshape(s, (-1, 1)) + tf.reshape(t, (1, -1))
        dist_4 = dist_4/lengthscale        
        pi = tf.constant(math.pi,dtype='float64')
        KK = (self.binned_g(dist_1)+self.binned_g(dist_2)-self.binned_g(dist_3)-self.binned_g(dist_4))
        KK = 0.5*tf.square(lengthscale)*KK
        
        return KK
    
    
    @params_as_tensors
    def K(self, X, X2=None):
        if X2 is None:
            X2 = X
        
        N = tf.size(X[:,self.index_dim])
        N4 = tf.size(X2[:,self.index_dim])
        
        #normal observations
        ind = tf.math.equal( X[:,self.index_dim], 0) 
        ind = tf.squeeze(ind)
        ind.set_shape([None])
        X1_11 = tf.boolean_mask(X[:,1],ind)
        X1_21 = tf.boolean_mask(X[:,2],ind)    
        
        ind = tf.math.equal( X2[:,self.index_dim], 0) 
        ind = tf.squeeze(ind)
        ind.set_shape([None])
        X2_11 = tf.boolean_mask(X2[:,1],ind)
        X2_21 = tf.boolean_mask(X2[:,2],ind)

        #binned observations
        ind = tf.math.equal( X[:,self.index_dim], 1) 
        ind = tf.squeeze(ind)
        ind.set_shape([None])
        X1_12 = tf.boolean_mask(X[:,1],ind)
        X1_22 = tf.boolean_mask(X[:,2],ind)
        
        ind = tf.math.equal( X2[:,self.index_dim], 1) 
        ind = tf.squeeze(ind)
        ind.set_shape([None])
        X2_12 = tf.boolean_mask(X2[:,1],ind)
        X2_22 = tf.boolean_mask(X2[:,2],ind)

        N2 = tf.size(X1_11)
        N3 = tf.size(X2_11)
        #SQE for normal observations
        dist_1 = tf.reshape(X1_11, (-1, 1)) - tf.reshape(X2_11, (1, -1))
        dist_2 = tf.reshape(X1_21, (-1, 1)) - tf.reshape(X2_21, (1, -1))

        K1 = self.variance*tf.exp(-tf.square(dist_1/self.lengthscale[0]))*tf.exp(-tf.square(dist_2/self.lengthscale[1]))

        #correlation between binned/normal observations
        K2 = self.binned_normal_correlation2(X1_11,X2_12,self.Lon,self.lengthscale[0])
        K2 = K2*self.binned_normal_correlation2(X1_21,X2_22,self.Lat,self.lengthscale[1])

        K2 = tf.sqrt(self.variance*self.variance_binned)*K2

        K3 = self.binned_normal_correlation(X1_12,X2_11,self.Lon,self.lengthscale[0])
        K3 = K3*self.binned_normal_correlation(X1_22,X2_21,self.Lat,self.lengthscale[1])

        K3 = tf.sqrt(self.variance*self.variance_binned)*K3  

        #binned covariance
        K4=self.binned_correlation(X1_12,X2_12,self.Lon,self.lengthscale[0])
        K4=K4*self.binned_correlation(X1_22,X2_22,self.Lat,self.lengthscale[1])
        K4= self.variance_binned*K4
        
        KK = tf.concat([K1, K2], 1)
        KK2 = tf.concat([K3, K4], 1)
        KK3 = tf.concat([KK,KK2], 0)


        return KK3
    @params_as_tensors
    def Kdiag(self, X):
        return tf.diag_part(self.K(X))


class binned_kernel_nonstationary(gpflow.kernels.Kernel):
    def __init__(self, input_dim, active_dims, index_dim,variance= 10.0, lengthscales=[1,1]):
        gpflow.kernels.Kernel.__init__(self, input_dim=input_dim, active_dims=active_dims)
        
        self.variance = gpflow.Param(variance, transform=gpflow.transforms.positive, dtype = 'float64')
        self.Lon = 0.74
        self.Lat = 1.64
        self.lengthscale = gpflow.Param(lengthscales, transform=gpflow.transforms.positive,dtype = 'float64')
        self.variance_binned = gpflow.Param(3, transform=gpflow.transforms.positive,dtype = 'float64')
        self.index_dim = index_dim
    
    def binned_normal_correlation(self, X1_11, X2_12,agg,lengthscale):

        dist_11 = tf.reshape(X1_11, (-1, 1)) - tf.reshape(X2_12, (1, -1))+agg/2
        dist_11 = dist_11/lengthscale
        dist_12 = -tf.reshape(X1_11, (-1, 1)) + tf.reshape(X2_12, (1, -1))+agg/2
        dist_12 = dist_12/lengthscale
        pi = tf.constant(math.pi,dtype='float64')
        KK = 0.5*tf.sqrt(pi)*lengthscale*(tf.math.erf(dist_11)+tf.math.erf(dist_12))
        
        return KK
    
    def binned_normal_correlation2(self, X1_11, X2_12,agg,lengthscale):

        dist_11 = -tf.reshape(X1_11, (-1, 1)) + tf.reshape(X2_12, (1, -1))+agg/2
        dist_11 = dist_11/lengthscale
        dist_12 = tf.reshape(X1_11, (-1, 1)) - tf.reshape(X2_12, (1, -1))+agg/2
        dist_12 = dist_12/lengthscale
        pi = tf.constant(math.pi,dtype='float64')
        KK = 0.5*tf.sqrt(pi)*lengthscale*(tf.math.erf(dist_11)+tf.math.erf(dist_12))
        
        return KK


    def binned_g(self,z):
        pi = tf.constant(math.pi,dtype='float64')
        tmp = z*tf.sqrt(pi)*tf.math.erf(z)+tf.exp(-tf.square(z))
        return tmp


    def binned_correlation(self, s, t,agg,lengthscale):

        dist_1 = tf.reshape(s, (-1, 1)) - tf.reshape(t, (1, -1))+agg
        dist_1 = dist_1/lengthscale
        dist_2 = -tf.reshape(s, (-1, 1)) + tf.reshape(t, (1, -1))+agg
        dist_2 = dist_2/lengthscale
        dist_3 = tf.reshape(s, (-1, 1)) - tf.reshape(t, (1, -1))
        dist_3 = dist_3/lengthscale
        dist_4 = -tf.reshape(s, (-1, 1)) + tf.reshape(t, (1, -1))
        dist_4 = dist_4/lengthscale        
        pi = tf.constant(math.pi,dtype='float64')
        KK = (self.binned_g(dist_1)+self.binned_g(dist_2)-self.binned_g(dist_3)-self.binned_g(dist_4))
        KK = 0.5*tf.square(lengthscale)*KK
        
        return KK
    
    
    @params_as_tensors
    def K(self, X, X2=None):
        if X2 is None:
            X2 = X
        
        N = tf.size(X[:,self.index_dim])
        N4 = tf.size(X2[:,self.index_dim])
        
        #normal observations
        ind = tf.math.equal( X[:,self.index_dim], 0) 
        ind = tf.squeeze(ind)
        ind.set_shape([None])
        X1_11 = tf.boolean_mask(X[:,1],ind)
        X1_21 = tf.boolean_mask(X[:,2],ind)    
        
        ind = tf.math.equal( X2[:,self.index_dim], 0) 
        ind = tf.squeeze(ind)
        ind.set_shape([None])
        X2_11 = tf.boolean_mask(X2[:,1],ind)
        X2_21 = tf.boolean_mask(X2[:,2],ind)

        #binned observations
        ind = tf.math.equal( X[:,self.index_dim], 1) 
        ind = tf.squeeze(ind)
        ind.set_shape([None])
        X1_12 = tf.boolean_mask(X[:,1],ind)
        X1_22 = tf.boolean_mask(X[:,2],ind)
        
        ind = tf.math.equal( X2[:,self.index_dim], 1) 
        ind = tf.squeeze(ind)
        ind.set_shape([None])
        X2_12 = tf.boolean_mask(X2[:,1],ind)
        X2_22 = tf.boolean_mask(X2[:,2],ind)

        N2 = tf.size(X1_11)
        N3 = tf.size(X2_11)
        #SQE for normal observations
        dist_1 = tf.reshape(X1_11, (-1, 1)) - tf.reshape(X2_11, (1, -1))
        dist_2 = tf.reshape(X1_21, (-1, 1)) - tf.reshape(X2_21, (1, -1))

        K1 = self.variance*tf.exp(-tf.square(dist_1/self.lengthscale[0]))*tf.exp(-tf.square(dist_2/self.lengthscale[1]))

        #correlation between binned/normal observations
        K2 = self.binned_normal_correlation2(X1_11,X2_12,self.Lon,self.lengthscale[0])
        K2 = K2*self.binned_normal_correlation2(X1_21,X2_22,self.Lat,self.lengthscale[1])

        K2 = tf.sqrt(self.variance*self.variance_binned)*K2

        K3 = self.binned_normal_correlation(X1_12,X2_11,self.Lon,self.lengthscale[0])
        K3 = K3*self.binned_normal_correlation(X1_22,X2_21,self.Lat,self.lengthscale[1])

        K3 = tf.sqrt(self.variance*self.variance_binned)*K3  

        #binned covariance
        K4=self.binned_correlation(X1_12,X2_12,self.Lon,self.lengthscale[0])
        K4=K4*self.binned_correlation(X1_22,X2_22,self.Lat,self.lengthscale[1])
        K4= self.variance_binned*K4
        
        KK = tf.concat([K1, K2], 1)
        KK2 = tf.concat([K3, K4], 1)
        KK3 = tf.concat([KK,KK2], 0)


        return KK3
    @params_as_tensors
    def Kdiag(self, X):
        return tf.diag_part(self.K(X))


        



class nsns_RQ(gpflow.kernels.Kernel):
    def __init__(self, input_dim, active_dims,variance= 1.0, lengthscales=[0.001, 1]):
        gpflow.kernels.Kernel.__init__(self, input_dim=input_dim, active_dims=active_dims)
        self.variance = gpflow.Param(variance, transform=gpflow.transforms.positive)
        a = lengthscales[0]*np.ones(input_dim)
        b = lengthscales[1]*np.ones(input_dim)
        self.lambda0 = gpflow.Param(0.1, transform=gpflow.transforms.positive)
        self.lambda1 = gpflow.Param(0.5, transform=gpflow.transforms.positive)
        self.lambda2 = gpflow.Param(0.5, transform=gpflow.transforms.positive)
        self.lengthscale_a = gpflow.Param(a, transform=gpflow.transforms.positive)
        self.lengthscale_b = gpflow.Param(b, transform=gpflow.transforms.positive)
     
    def hyper_function(self, X, input_dim):
        return self.lengthscale_b[input_dim] + self.lengthscale_a[input_dim]*X
    
    @params_as_tensors
    def K(self, X, X2=None):
        if X2 is None:
            X2 = X       
        K = 1.0
        lengthscale = tf.abs(self.hyper_function(X[:,0],0))+0.001
        lengthscale2 = tf.abs(self.hyper_function(X2[:, 0],0))+0.001
        dist2 = tf.reshape(lengthscale, (-1, 1)) + tf.reshape(lengthscale2, (1, -1))
        dist_1 = tf.reshape(X[:,0], (-1, 1)) - tf.reshape(X2[:, 0], (1, -1))
        dist_1 = tf.square(dist_1)/dist2

        lengthscale = tf.abs(self.hyper_function(X[:,1],1))+0.001
        lengthscale2 = tf.abs(self.hyper_function(X2[:, 1],1))+0.001
        dist2 = tf.reshape(lengthscale, (-1, 1)) + tf.reshape(lengthscale2, (1, -1))
        dist_2 = tf.reshape(X[:,1], (-1, 1)) - tf.reshape(X2[:, 1], (1, -1))
        dist_2 = tf.square(dist_2)/dist2
        
        
        K1 = tf.pow(1+dist_1+dist_2,-self.lambda0)
        K2 = tf.pow(1+dist_1,-self.lambda1)
        K3 = tf.pow(1+dist_2,-self.lambda2)
            
        return self.variance*K1*K2*K3#tf.square(tf.reshape(X, (-1, 1)) - tf.reshape(X, (1, -1)))
    
    @params_as_tensors
    def Kdiag(self, X):
        return tf.fill(tf.stack([tf.shape(X)[0]]), tf.squeeze(self.variance))


