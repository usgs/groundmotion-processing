# Baseline correction

The `detrend` method allows for an option of setting the `detrending_method` option
as `baseline_sixth_order`. This applies an implementation of the method described by 
Ancheta et al. ([2013](https://www.pge.com/includes/docs/pdfs/shared/edusafety/systemworks/dcpp/SSHAC/workshops/ground_motion/GMC_0103_Ancheta_PEER_NGAW2_DATABASE.pdf)).
This method fits a sixth-order polynomial to the displacement time series in which the
zeroth- and first-order terms to be zero. The second derivative of the fit polynomial
is then removed from the acceleration time series. 
