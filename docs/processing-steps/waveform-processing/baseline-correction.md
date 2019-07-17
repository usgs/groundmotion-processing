# Baseline correction

The `detrend` method allows for an option of setting the `detrending_method` option
as `baseline_sixth_order`. This applies is an implementation of the method described
by Ancheta et al. ([2013](https://www.pge.com/includes/docs/pdfs/shared/edusafety/systemworks/dcpp/SSHAC/workshops/ground_motion/GMC_0103_Ancheta_PEER_NGAW2_DATABASE.pdf)),
where a sixth-order polynomial to the displacement time series, and sets the zeroth- 
and first-order terms to be zero. The second derivative of the fit polynomial is then
removed from the acceleration time series. 
