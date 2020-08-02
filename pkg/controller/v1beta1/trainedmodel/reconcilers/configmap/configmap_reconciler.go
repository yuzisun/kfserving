/*
Copyright 2020 kubeflow.org.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package configmap

import (
	v1beta1api "github.com/kubeflow/kfserving/pkg/apis/serving/v1beta1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/equality"
	"k8s.io/apimachinery/pkg/runtime"
	knservingv1 "knative.dev/serving/pkg/apis/serving/v1"
	"sigs.k8s.io/controller-runtime/pkg/client"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

var log = logf.Log.WithName("Reconciler")

type ConfigMapReconciler struct {
	client client.Client
	scheme *runtime.Scheme
}

func NewConfigMapReconciler(client client.Client, scheme *runtime.Scheme) *ConfigMapReconciler {
	return &ConfigMapReconciler{
		client: client,
		scheme: scheme,
	}
}

func (r *ConfigMapReconciler) Reconcile(desired *corev1.ConfigMap, trainedModel *v1beta1api.TrainedModel) (*corev1.ConfigMap, error) {
	//TODO make sure this reconcile loop will be triggered by Create/Delete/Update event for TrainedModel
	//TODO update an existing configmap to add/remove a model in it

	// check if the trainedModel has a delete timestamp
	// if has -> delete from configmap
	//  if not have delete timestamp
	//     addOrupdate configMap

	return nil, nil
}

func semanticEquals(desiredService, service *knservingv1.Service) bool {
	return equality.Semantic.DeepEqual(desiredService.Spec.ConfigurationSpec, service.Spec.ConfigurationSpec) &&
		equality.Semantic.DeepEqual(desiredService.ObjectMeta.Labels, service.ObjectMeta.Labels)
}
